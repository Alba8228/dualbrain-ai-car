#ifndef __USART_H_
#define __USART_H_

#include "stm32f10x.h"
#include "stdio.h"


void USART_Config(uint32_t brr);
void USART_SendString(char *str);

#endif

