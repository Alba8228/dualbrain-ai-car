#include "led.h"
//PCO~2

void LED_Config(void)
{
	//1.开GPIOC时钟
	 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC,ENABLE);
	//定义结构体并初始化
   GPIO_InitTypeDef LED_InitStruct = {0};
	 //模式
	LED_InitStruct.GPIO_Mode = GPIO_Mode_Out_PP;
	//引脚
	LED_InitStruct.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_2;
	//速率
	LED_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOC,&LED_InitStruct);
	
}