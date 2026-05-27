#include "beep.h"
void BEEP_Config(void)
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);
	GPIO_InitTypeDef BEEP_InitStruct={0};
	BEEP_InitStruct.GPIO_Mode=GPIO_Mode_Out_PP;
	BEEP_InitStruct.GPIO_Pin=GPIO_Pin_15;
	BEEP_InitStruct.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOA,&BEEP_InitStruct);
	BEEP_OFF(BEEP_Port,BEEP_Pin);
}