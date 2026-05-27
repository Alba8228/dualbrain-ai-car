#include "usart1.h"
//PA9：输出模式  复用推挽模式
//PA10：输入模式  浮空输入
void USART_Config(uint32_t brr)
{
	//开时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);
	//配置发送和接收相关的GPIO口
	//PA10输入模式
	GPIO_InitTypeDef GPIOA_USART_InitStruct = {0};
	GPIOA_USART_InitStruct.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIOA_USART_InitStruct.GPIO_Pin = GPIO_Pin_10;
//	GPIOA_USART_InitStruct.GPIO_Speed
	GPIO_Init(GPIOA,&GPIOA_USART_InitStruct);
	//PA9 输出模式
	GPIOA_USART_InitStruct.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIOA_USART_InitStruct.GPIO_Pin = GPIO_Pin_9;
	GPIOA_USART_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA,&GPIOA_USART_InitStruct);
	//开串口的时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1,ENABLE);
	//定义一个结构体并对他初始化
	USART_InitTypeDef USART1_InitStruct = {0};
	//波特率
	USART1_InitStruct.USART_BaudRate = brr;
	//硬件流控制,这里选择无硬件流
	USART1_InitStruct.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	//模式:发送和接收
	USART1_InitStruct.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	//校验位
	USART1_InitStruct.USART_Parity = USART_Parity_No;
	//停止位：1位
	USART1_InitStruct.USART_StopBits = USART_StopBits_1;
	//数据长度：8位
	USART1_InitStruct.USART_WordLength = USART_WordLength_8b;
	USART_Init(USART1,&USART1_InitStruct);
	//使能串口
	USART_Cmd(USART1,ENABLE);
}
//封装单字节的发送函数
void USART_Send_DataBit(char ch)
{
	//判断上一个数据有没有发送完成，如果没有发送完成
	//那么就等待上一个一个数据发送完成
	while(USART_GetFlagStatus(USART1,USART_FLAG_TC) == RESET);
	//上一个数据发送完成，我就发送新的数据
	USART_SendData(USART1,ch);
}
//字符串的发送函数
void USART_SendString(char *str)
{
	//字符串的结尾是'\0'
	while(*str != '\0')
	{
		USART_Send_DataBit(*str);
		str++;
	}
}
//重定向printf函数
int fputc(int ch,FILE *fp)
{
	USART_Send_DataBit(ch);
	return ch;
}

