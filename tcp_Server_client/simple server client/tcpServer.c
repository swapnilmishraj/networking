#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>
#include<sys/socket.h>
#include<sys/types.h>
//#includea<netinet/in.h>
#include<arpa/inet.h>
#include<signal.h>

int ssd;
sigset_t set1;
struct sigaction act1;


void my_quit_handler(int signo)
{
	printf("signal recieved is:%d\n",signo);
	close(ssd);
	exit(0);
}


int main()
{

	sigfillset(&set1);
	sigdelset(&set1,SIGQUIT);
	sigdelset(&set1,SIGINT);
	sigdelset(&set1,SIGPIPE);
	
	sigprocmask(SIG_SETMASK,&set1,NULL);
		
	act1.sa_handler=my_quit_handler;
	act1.sa_mask=set1;
	

	sigaction(SIGQUIT, &act1, NULL);
	sigaction(SIGINT, &act1, NULL);
	sigaction(SIGPIPE, &act1, NULL);



	//create a simple socket
	int ret,sport=1500;
	ssd=socket(AF_INET, SOCK_STREAM,0);	//creates an endpoint and returns a socket descriptor
	if(ssd<0){	perror("socket error");	exit(1);	}
	
	//bind the socket to an address
	

	struct sockaddr_in saddr;
	saddr.sin_family=AF_INET;
	saddr.sin_port=htons(sport);
	saddr.sin_addr.s_addr=inet_addr("127.0.0.1");
//	memset(&saddr.sin_zero, '\0', sizeof(saddr.sin_zero));
	bzero(&saddr.sin_zero,sizeof(saddr.sin_zero));	
	ret=bind(ssd, (struct sockaddr *)&saddr,sizeof(saddr));
	if(ret<0){	perror("bind");	exit(2);	}
	
	
	//listen to any incoming connection
	int backlog=5;
	ret=listen(ssd,backlog);
	if(ret<0){	perror("listen");	exit(2);	}

	//accept
	struct sockaddr_in caddr;
	socklen_t clen=sizeof(caddr);
	int csd=accept(ssd, (struct sockaddr *)&caddr, &clen);
	if(csd<0){	perror("accept error");	exit(3);	}
	
	printf("a client got connected from %s:%d\n",inet_ntoa(caddr.sin_addr),ntohs(caddr.sin_port));
	
	char buf[100];
	
	
	//send and recv
	while(1)
	{
		int nbytes=recv(csd,buf, sizeof(buf), 0);
		if(nbytes<0){	perror("recv error");	exit(4);	}
		if(nbytes==0){
			printf("recieved bytes is 0\n");
			break;
		}
		if(strncmp("exit",buf,4)==0){
			break;	
		}
		else{
			nbytes=send(csd,buf,nbytes,0);
			if(nbytes<0){	perror("send error");	exit(4);	}
		}
		printf("enter something\n");
		scanf("%s",buf);
		nbytes=send(csd,buf,nbytes,0);
		if(nbytes<0){	perror("send error");	exit(4);	}
		printf("i reached here\n");
		
	}
	close(ssd);
		
	return 0;	
		
}
