#ifndef __TRCAK_H_
#define __TRCAK_H_

#include "stm32f10x.h"
//¼ì²âµ½ºÚÏß¶Á1 °×Ïß¶Á0
#define Track_Out1() (GPIO_ReadInputDataBit(GPIOC,GPIO_Pin_7))
#define Track_Out2() (GPIO_ReadInputDataBit(GPIOC,GPIO_Pin_8))
#define Track_Out3() (GPIO_ReadInputDataBit(GPIOC,GPIO_Pin_9))
#define Track_Out4() (GPIO_ReadInputDataBit(GPIOC,GPIO_Pin_10))
#define Track_Out5() (GPIO_ReadInputDataBit(GPIOC,GPIO_Pin_11))
//A:00001---->10000
//B:00001---->01000
//A||B  ----->11000
#define Track_GetValue() ((Track_Out1()<<4) |(Track_Out2()<<3) | (Track_Out3()<<2) | (Track_Out4()<<1) |(Track_Out5()))


void Track_Find_Line(void);
void TRACK_Config(void);

#endif


