#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <net/if.h>
#include <net/if_dl.h>
#include <net/route.h>
#include <unistd.h>
#include <poll.h>
#include <errno.h>
#include <err.h>
#include <fcntl.h>

#define TARGETIFNAM "awdl0"

// Large enough for any routing message; short reads truncate the message.
static uint8_t rtmsgbuff[2048];

// Read the interface's current flags and clear IFF_UP if set.
// Always uses fresh flags so concurrent flag changes are not clobbered.
// Returns 0 on success (or already down), -1 with errno set on failure.
static int awdl_down(int iocfd) {
	struct ifreq ifr;
	memset(&ifr, 0, sizeof(ifr));
	strlcpy(ifr.ifr_name, TARGETIFNAM, sizeof(ifr.ifr_name));

	if (ioctl(iocfd, SIOCGIFFLAGS, &ifr) < 0) {
		return -1;
	}
	if (!(ifr.ifr_flags & IFF_UP)) {
		return 0;
	}
	ifr.ifr_flags &= ~IFF_UP;
	return ioctl(iocfd, SIOCSIFFLAGS, &ifr);
}

int main(void) {
	// Effective UID 0 is required: either run as root (e.g. via launchd)
	// or via a root-owned setuid binary.
	if (geteuid() != 0) {
		errx(1, "Must run as root (or as a root-owned setuid binary).");
	}

	// get interface ID
	unsigned int ifidx = if_nametoindex(TARGETIFNAM);
	if (!ifidx) {
		err(1, "Error getting index of " TARGETIFNAM);
	}

	// socket to monitor network interface changes
	int rtfd = socket(AF_ROUTE, SOCK_RAW, 0);
	if (rtfd < 0) {
		err(1, "Error creating AF_ROUTE socket");
	}
	if (fcntl(rtfd, F_SETFL, O_NONBLOCK) < 0) {
		err(1, "Error setting nonblock on AF_ROUTE socket");
	}

	// socket to perform ioctl to set interface flags
	int iocfd = socket(AF_INET, SOCK_DGRAM, 0);
	if (iocfd < 0) {
		err(1, "Error creating AF_INET socket");
	}

	// kill awdl on program startup straight away!
	if (awdl_down(iocfd) < 0) {
		err(1, "Error initially disabling " TARGETIFNAM);
	}

	struct pollfd prt = { .fd = rtfd, .events = POLLIN };
	for (;;) {
		if (poll(&prt, 1, -1) < 0) {
			if (errno == EINTR) {
				continue;
			}
			err(1, "Error polling AF_ROUTE socket");
		}

		// Drain all queued messages, then act at most once.
		int need_check = 0;
		for (;;) {
			ssize_t len = read(rtfd, rtmsgbuff, sizeof(rtmsgbuff));
			if (len < 0) {
				if (errno == EINTR) {
					continue;
				} else if (errno == EAGAIN || errno == EWOULDBLOCK) {
					break;
				} else if (errno == ENOBUFS) {
					// Socket overflowed and messages were lost: resync.
					need_check = 1;
					continue;
				}
				err(1, "Error reading AF_ROUTE socket");
			}

			struct rt_msghdr *rtmsg = (void *)rtmsgbuff;
			if ((size_t)len < sizeof(struct if_msghdr)
				|| rtmsg->rtm_version != RTM_VERSION
				|| rtmsg->rtm_type != RTM_IFINFO) {
				continue;
			}

			struct if_msghdr *ifmsg = (void *)rtmsgbuff;
			if (ifmsg->ifm_index != ifidx) {
				// awdl0 may have been recreated with a new index.
				unsigned int cur = if_nametoindex(TARGETIFNAM);
				if (!cur || cur == ifidx || ifmsg->ifm_index != cur) {
					continue;
				}
				ifidx = cur;
			}

			if (ifmsg->ifm_flags & IFF_UP) {
				need_check = 1;
			}
		}

		if (need_check && awdl_down(iocfd) < 0) {
			int saved_errno = errno;
			// Don't exit: a respawn is throttled by launchd and would leave
			// AWDL up in the meantime. The next event retries.
			warn("Error turning down " TARGETIFNAM);
			if (saved_errno == ENXIO) {
				unsigned int cur = if_nametoindex(TARGETIFNAM);
				if (cur) {
					ifidx = cur;
				}
			}
		}
	}
}
