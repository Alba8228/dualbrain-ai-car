#include "wifi.h"
#include "stdio.h"
#include "string.h"
#include "motor.h"
#include "sg90.h"

void WIFI_Config(void)
{
	//开时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);
	//配置IO
	GPIO_InitTypeDef GPIO_InitStructure={0};
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
	GPIO_Init(GPIOB, &GPIO_InitStructure);
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_11;
	GPIO_Init(GPIOB, &GPIO_InitStructure);
	//配置USART3
	USART_InitTypeDef USART_InitStructuer={0};
	USART_InitStructuer.USART_BaudRate = 9600;
	USART_InitStructuer.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructuer.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_InitStructuer.USART_Parity = USART_Parity_No;
	USART_InitStructuer.USART_StopBits = USART_StopBits_1;
	USART_InitStructuer.USART_WordLength = USART_WordLength_8b;
	USART_Init(USART3, &USART_InitStructuer);
	//使能接收中断
	USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);
	USART_ITConfig(USART3, USART_IT_IDLE, ENABLE);
	//配置NVIC
	NVIC_InitTypeDef NVIC_InitStructure;
	NVIC_InitStructure.NVIC_IRQChannel = USART3_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0x00;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0x00;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);
	//使能串口
	USART_Cmd(USART3, ENABLE);
}
__WIFI_TYPE wifi = {0};

void USART3_IRQHandler(void)
{
	uint8_t data = 0;
	if(USART_GetFlagStatus(USART3, USART_FLAG_RXNE) == SET)
	{
		data = USART3->DR;
		USART1->DR = data;
		if(wifi.recvOver == 0) {
			wifi.recvData[wifi.recvCount++] = data;
		}
	}
	if(USART_GetFlagStatus(USART3, USART_FLAG_IDLE) == SET)
	{
		USART3->SR;
		data = USART3->DR;
		wifi.recvOver = 1;
	}	
}

//解析wifi收到的数据 一帧信息6个字节 [0]=0xAA [1]=0x55 
/*
帧头[0][1]+小车方向[2]+舵机方向[3]+小车速度[4]+校验和[5]
wifi.recvData[0~5]
*/
void WIFI_Analysis(void)
{
	uint8_t check = 0;
	if(wifi.recvOver == 0)	return;//判断是否接收完成
	if(wifi.recvCount == 0) //判断是否接收到数据
	{
		wifi.recvOver = 0;//清除标志位
		return ;
	}
	//判断是否接收够5个字节
	if(wifi.recvCount < 5)
	{
		wifi.recvOver = 0;
		goto err;
	}
	//判断校验和
	check = wifi.recvData[0]+wifi.recvData[1]+wifi.recvData[2]+wifi.recvData[3]+wifi.recvData[4];
	if(check != wifi.recvData[5])
	{
		goto err;
	}
	//给小车设置运动状态
	switch(wifi.recvData[2])
	{
		case 0x00:Car_Stop();break;
		case 0x01:CAR_Forward(500);break;
		case 0x02:CAR_Back(500);break;
		case 0x03:Car_Left_Big(400);break;
		case 0x04:Car_Right_Big(400);break;
		default:Car_Stop();break;
	}
	//给云台设置状态
	switch(wifi.recvData[3])
	{
		case 0x05:SteerDir = SteerStop;break;
		case 0x06:SteerDir = SteerLeft;break;
		case 0x07:SteerDir = SteerRight;break;
		case 0x08:SteerDir = SteerUp;break;
		case 0x09:SteerDir = SteerDown;break;
		default:SteerDir = SteerStop;break;
	}
	err:
		memset(wifi.recvData, 0, 256);
		wifi.recvCount = 0;
		wifi.recvOver = 0;
}
