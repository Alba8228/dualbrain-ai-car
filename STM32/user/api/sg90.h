#ifndef _STEER_H_
#define _STEER_H_

#include "stm32f10x.h"

/*
 **********************************************
 以下程序是舵机控制程序
 ***********************************************/

typedef enum {
	SteerStop = '8',
	SteerLeft = '7',
	SteerRight = '9',
	SteerUp = '5',
	SteerDown = '0',
}__STEER_DIR;

extern uint8_t SteerDir;

void Steer_Init(void);
void Tim1_SteerInit(u16 psc, u16 arr, u16 ccr);
void Steer_SetPWM(uint8_t steer, uint16_t pwm) ;
void Steer_SetAngle(uint8_t steer, int angle) ;
void Steer_Control(void);

#endif

