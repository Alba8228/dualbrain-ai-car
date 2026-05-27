#include "blue.h"
#include "stdio.h"
#include "motor.h"
#include "string.h"
#include "beep.h"
//PA2  TX
//PA3  RX
void Blue_Config(void)
{
	//开GPIO口时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);
	//定义结构体并赋值
	GPIO_InitTypeDef Blue_InitStruct = {0};
	Blue_InitStruct.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	Blue_InitStruct.GPIO_Pin = GPIO_Pin_3;
	GPIO_Init(GPIOA,&Blue_InitStruct);
	//PA2
	Blue_InitStruct.GPIO_Mode = GPIO_Mode_AF_PP;
	Blue_InitStruct.GPIO_Pin = GPIO_Pin_2;
	Blue_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA,&Blue_InitStruct);
	//开串口2的时钟。USART2 在 APB1 上
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2,ENABLE);
	//定义串口结构体并初始化
	USART_InitTypeDef USART2_InitStruct = {0};
	//波特率,根据手册进行配置9600
	USART2_InitStruct.USART_BaudRate = 9600;
	//硬件流，这里选择无需硬件流
	USART2_InitStruct.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	//模式选择发送和接收
	USART2_InitStruct.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	//奇偶校验位
	USART2_InitStruct.USART_Parity = USART_Parity_No;
	//停止位
	USART2_InitStruct.USART_StopBits = USART_StopBits_1;
	//数据位长度
	USART2_InitStruct.USART_WordLength = USART_WordLength_8b;
	USART_Init(USART2,&USART2_InitStruct);
	//使能串口
	USART_Cmd(USART2,ENABLE);
	//使能接收中断和空闲中断
	USART_ITConfig(USART2,USART_IT_IDLE,ENABLE);
	USART_ITConfig(USART2,USART_IT_RXNE,ENABLE);
	//定义中断结构体并完成相关配置
	NVIC_InitTypeDef NVIC_InitStruct = {0};
	//配置中断通道
	NVIC_InitStruct.NVIC_IRQChannel = USART2_IRQn;
	//使能中断
	NVIC_InitStruct.NVIC_IRQChannelCmd = ENABLE;
	//抢占优先级
	NVIC_InitStruct.NVIC_IRQChannelPreemptionPriority = 2;
	//响应优先级
	NVIC_InitStruct.NVIC_IRQChannelSubPriority = 3;
	NVIC_Init(&NVIC_InitStruct);
}
uint8_t Receive_Buff[20] = {0};
uint8_t Receive_Count = 0;
//数据接收完成的标志位
uint8_t Blue_Flag = 0;
//这个函数名不能自己命名
void USART2_IRQHandler(void)
{
	//先判断是触发接收中断还是空闲中断
	if(USART_GetITStatus(USART2,USART_IT_RXNE) == SET)
	{
		//说明触发接收中断
		USART_ClearITPendingBit(USART2,USART_IT_RXNE);
		//调用函数读取收到的数据
		uint8_t data = USART_ReceiveData(USART2);
		//通过串口1把接收到的数据进行回显
		USART1->DR = data;
		//把接收到的数据存储起来
		Receive_Buff[Receive_Count] = data;
		Receive_Count ++;
	}
	//判断是否完成空闲中断
	if(USART_GetITStatus(USART2,USART_IT_IDLE) == SET)
	{
		//已经触发空闲中断
		//空闲中断的标志位先读SR寄存器，再读DR寄存器
		USART2->SR;
		USART2->DR;
		Blue_Flag = 1;
	}
}

//解析函数
void Blue_Analysis(void)
{
	if(Blue_Flag ==1)//数据接收完成
	{
		if(Receive_Buff[0]==0xAA &&Receive_Buff[1] ==0x55)
		{
			switch(Receive_Buff[2])
			 { 
				case 1:
					CAR_Forward(666);
			    break;
				case 2:
					CAR_Back(666);
				break;
				case 3:
					Car_Left_Mid(666);
				break;
				case 4:
					Car_Right_Mid(666);
					
					break;
				case 5:
					Car_Stop();
					break;
			 } 
		}
		Blue_Flag = 0;
		Receive_Count = 0;
		memset(Receive_Buff,0,sizeof(Receive_Buff));
	}
}

void USART2_Send_DataBit(char ch)
{
	//串口2的发送函数
	USART_SendData(USART2,ch);
	//判断数据有没有发送完成
	while(USART_GetFlagStatus(USART2,USART_FLAG_TXE) == RESET);
}
void USART2_SendStr(char *str)
{
	//字符串的结尾是以\0结尾的
	while(*str != '\0')
	{
		USART2_Send_DataBit(*str);
		str++;
	}
}

void BLUE_Set_Name(char *name)
{
	char name_buff[20] = {0};
	sprintf(name_buff,"AT+NAME%s\r\n",name);
	USART2_SendStr(name_buff);
}



