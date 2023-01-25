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

uint8_t rtmsgbuff[sizeof(struct rt_msghdr) + sizeof(struct if_msghdr)];

int main() {
	// check root
	if (getuid() != 0) {
		// try setuid
		if (setuid(0) < 0) {
			errx(1, "Error escalating permission to root. Either run this app as root"
				" or set setuid bit with root permission.");
		}
	}

	// get interface ID
	int ifidx = if_nametoindex(TARGETIFNAM);
	if (!ifidx) {
		err(1, "Error getting interface name");
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

	struct ifreq ifr = {0};
	strlcpy(ifr.ifr_name, TARGETIFNAM, IFNAMSIZ);

	// kill awdl on program startup straight away!
	if (ioctl(iocfd, SIOCGIFFLAGS, &ifr) < 0) {
		err(1, "Error getting initial flags");
	}
	if (ifr.ifr_flags & IFF_UP) {
		ifr.ifr_flags &= ~IFF_UP;
		if (ioctl(iocfd, SIOCSIFFLAGS, &ifr) < 0) {
			err(1, "Error initial disable interface");
		}
	}

	struct pollfd prt;
	prt.fd = rtfd;
	prt.events = POLLIN;
	for(;;) {
		if (poll(&prt, 1, -1) < 0) {
			if (errno == EINTR) {
				continue;
			}
			err(1, "Error polling AF_ROUTE socket");
		}

		// for all queued reads, we take the final value flag and do SIOCSIFFLAGS once
		int ifflag = 0;
		for(ssize_t len = 0;;) {
			len = read(rtfd, rtmsgbuff, sizeof(rtmsgbuff));
			if (len < 0) {
				if (errno == EINTR) {
					continue;
				} else if (errno == EAGAIN) {
					break;
				}
				err(1, "Error reading AF_ROUTE socket");
			}

			struct rt_msghdr * rtmsg = (void *)rtmsgbuff;
			if (rtmsg->rtm_type != RTM_IFINFO) {
				continue;
			}

			struct if_msghdr * ifmsg = (void *)rtmsg;
			if (ifmsg->ifm_index != ifidx) {
				// not the interface that we want
				continue;
			}

			ifflag = ifmsg->ifm_flags;
		}

		if (ifflag & IFF_UP) {
			// AWDL is up (and running)! We must stop it!
			ifr.ifr_flags = ifflag & ~IFF_UP;
			if (ioctl(iocfd, SIOCSIFFLAGS, &ifr) < 0) {
				err(1, "Error turning down interface");
			}
		}
	}
}
