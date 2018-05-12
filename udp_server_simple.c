nclude<stdio.h>
#include<unistd.h>
#include<stdlib.h>
#include<string.h>
#include<sys/socket.h>
#include <sys/types.h>  
#include <arpa/inet.h>
#include<time.h>
int main()
{
	time_t mytime; 
	int send_sd,ret,sport=1500;
	char buf[100];
	//AF_INET --> IPv4     SOCK_DGRAM--> UDP
	send_sd=socket(AF_INET,SOCK_DGRAM,0);
	if (send_sd < 0){
		perror("socket error");
		exit(1);
	}
	printf("send_sd created\n");
	struct sockaddr_in saddr,caddr;
	saddr.sin_family=AF_INET;
	saddr.sin_port=htons(sport);
	saddr.sin_addr.s_addr=inet_addr("127.0.0.1");
	bzero(&saddr.sin_zero,sizeof(saddr.sin_zero));
	
	/* 
	* bind: associate the parent socket with a port 
	*/
	ret=bind(send_sd, (struct sockaddr *)&saddr,sizeof(saddr));
	
	if(ret<0){
		perror("bind");
		exit(2);
	}
	
	printf("bind done\n");

	socklen_t clen;
	
		/*mytime= time(NULL);
		strcpy(buf,ctime(&mytime));
		printf("the time is:%s and size is:%d\n",buf,strlen(buf));
		*/
	/* 
   	 * main loop: wait for a datagram, then echo it
   	 */
	while(1){
		/*
     	 	 * recvfrom: receive a UDP datagram from a client
     		 */
		ret=recvfrom(send_sd, buf, sizeof(buf), 0,(struct sockaddr*)&caddr, &clen);
		
		mytime= time(NULL);
		strcpy(buf,ctime(&mytime));
		printf("the time is:%s and size is:%d\n",buf,strlen(buf));
		int len=strlen(buf);
		int nbytes=sendto(send_sd, buf, len, 0,(struct sockaddr *)&caddr, clen);

		if(nbytes<0){
			perror("fail to send\n");
			exit(4);
		}
		if(nbytes==0){
			break;
		}
		
		if(strncmp("exit",buf,4)==0)
			break;
	
	}
	//close(csd);	
	close(send_sd);	

	return 0;
}
