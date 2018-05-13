#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>
#include<sys/socket.h>
#include<sys/types.h>
//#includea<netinet/in.h>
#include<arpa/inet.h>
#include<signal.h>

int csd;
sigset_t set1;
struct sigaction act1;


void my_quit_handler(void)
{
	
	close(csd);
	exit(0);
}


int main()
{

	sigfillset(&set1);
	sigdelset(&set1,SIGQUIT);
	sigdelset(&set1,SIGINT);
	sigprocmask(SIG_SETMASK,&set1,NULL);
		
	act1.sa_handler=my_quit_handler;
	act1.sa_mask=set1;

	sigaction(SIGQUIT, &act1, NULL);
	sigaction(SIGINT, &act1, NULL);


	//create a simple socket
	int ret,sport=1500;
	csd=socket(AF_INET, SOCK_STREAM,0);	//creates an endpoint and returns a socket descriptor
	if(csd<0){	perror("socket error");	exit(1);	}
	
	//bind the socket to an address
	

	struct sockaddr_in caddr;
	caddr.sin_family=AF_INET;
	caddr.sin_port=htons(0);
	caddr.sin_addr.s_addr=INADDR_ANY;
	memset(&caddr.sin_zero, '\0', sizeof(caddr.sin_zero));
	//bzero(&saddr.sin_zero,sizeof(saddr.sin_zero));	
	ret=bind(csd, (struct sockaddr *)&caddr,sizeof(caddr));
	if(ret<0){	perror("bind");	exit(2);	}
	
	struct sockaddr_in saddr;
	saddr.sin_family=AF_INET;
	saddr.sin_port=htons(1500);
	saddr.sin_addr.s_addr=inet_addr("127.0.0.1");
	memset(&saddr.sin_zero, '\0', sizeof(saddr.sin_zero));
	bzero(&saddr.sin_zero,sizeof(saddr.sin_zero));	
	
	ret=connect(csd,(struct sockaddr *)&saddr, sizeof(saddr));



	printf("a client got connected from %s:%d\n",inet_ntoa(caddr.sin_addr),ntohs(caddr.sin_port));
	
	char buf[100];
	
	
	//send and recv
	while(1)
	{

		int nbytes;

		printf("input to send\n");
		scanf("%s",buf);
		
		nbytes=send(csd,buf,strlen(buf),0);
		if(nbytes<0){	perror("send error");	exit(4);	}



		nbytes=recv(csd,buf, sizeof(buf), 0);
		if(nbytes<0){	perror("recv error");	exit(4);	}
		if(nbytes==0){
			break;
		}
		if(strncmp("exit",buf,4)==0){
			break;	
		}
		else{

			printf("recieved:%s\n",buf);
			}
		
	}
	close(csd);
		
	return 0;	
		
}
