#ifndef __BEEP_H_
#define __BEEP_H_

#include "stm32f10x.h"
#define BEEP_Port GPIOA
#define BEEP_Pin GPIO_Pin_15

//#define LED2_Port GPIOC
//#define LED2_Pin GPIO_Pin_1

//#define LED3_Port GPIOC
//#define LED3_Pin GPIO_Pin_2

#define BEEP_ON(port,pin) GPIO_WriteBit(port,pin,1)
#define BEEP_OFF(port,pin) GPIO_WriteBit(port,pin,0)
//#define LEDX_Toggle(port,pin) (port->ODR^=pin)
void BEEP_Config(void);
#endif

