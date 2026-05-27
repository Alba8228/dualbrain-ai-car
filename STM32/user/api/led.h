#ifndef __LED_H_
#define __LED_H_

#include "stm32f10x.h"

#define LED1_Port GPIOC
#define LED1_Pin GPIO_Pin_0

#define LED2_Port GPIOC
#define LED2_Pin GPIO_Pin_1

#define LED3_Port GPIOC
#define LED3_Pin GPIO_Pin_2

#define LEDX_ON(port,pin) GPIO_WriteBit(port,pin,0)
#define LEDX_OFF(port,pin) GPIO_WriteBit(port,pin,1)
#define LEDX_Toggle(port,pin) (port->ODR^=pin)

void LED_Config(void);
#endif