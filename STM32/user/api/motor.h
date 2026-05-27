#ifndef _CAR_MOTOR_H_
#define _CAR_MOTOR_H_

#include "stm32f10x.h"
//左前轮
#define Motor_Left_Fr_F(speed) (TIM_SetCompare1(TIM3,speed),TIM_SetCompare2(TIM3,0))
#define Motor_Left_Fr_B(speed) (TIM_SetCompare1(TIM3,0),TIM_SetCompare2(TIM3,speed))
//右后轮
#define Motor_Right_Back_F(speed) (TIM_SetCompare3(TIM3,speed),TIM_SetCompare4(TIM3,0))
#define Motor_Right_Back_B(speed) (TIM_SetCompare3(TIM3,0),TIM_SetCompare4(TIM3,speed))
//左后轮
#define Motor_Left_Back_F(speed) (TIM_SetCompare1(TIM4,speed),TIM_SetCompare2(TIM4,0))
#define Motor_Left_Back_B(speed) (TIM_SetCompare1(TIM4,0),TIM_SetCompare2(TIM4,speed))
//右前轮
#define Motor_Right_Fr_F(speed) (TIM_SetCompare3(TIM4,speed),TIM_SetCompare4(TIM4,0))
#define Motor_Right_Fr_B(speed) (TIM_SetCompare3(TIM4,0),TIM_SetCompare4(TIM4,speed))

void CAR_Motor_Config(void);
void CAR_Forward(uint16_t speed);
void CAR_Back(uint16_t speed);

void Car_Right_Big(uint16_t speed);
void Car_Right_Mid(uint16_t speed);
void Car_Right_Small(uint16_t speed);
//差速左转
void Car_Left_Big(uint16_t speed);
//左转中弯
void Car_Left_Mid(uint16_t speed);
//左转小弯
void Car_Left_Small(uint16_t speed);
void Car_Stop(void);
#endif
