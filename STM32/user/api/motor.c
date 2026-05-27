#include "motor.h"
//PA6 TIM3_CH1      PB6  TIM4_CH1
//PA7 TIM3_CH2      PB7  TIM4_CH2
//PB0 TIM3_CH3      PB8  TIM4_CH3
//PB1 TIM3_CH4      PB9  TIM4_CH4
void CAR_Motor_Config(void)
{
	//配置GPIO口
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB,ENABLE);
	//定义结构体并进行配置
	GPIO_InitTypeDef MOTOR_InitStruct = {0};
	MOTOR_InitStruct.GPIO_Mode = GPIO_Mode_AF_PP;
	MOTOR_InitStruct.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;
	MOTOR_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA,&MOTOR_InitStruct);
	//配置PB相关的引脚
	MOTOR_InitStruct.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_6 | GPIO_Pin_7 | GPIO_Pin_8 | GPIO_Pin_9;
	GPIO_Init(GPIOB,&MOTOR_InitStruct);
	//开TIM3&&TIM4的时钟
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3 | RCC_APB1Periph_TIM4,ENABLE);
	//定义结构体，并配置成员
	TIM_TimeBaseInitTypeDef TIM_InitStruct = {0};
	//输入分频，用于输入捕获，这里默认不分频
	TIM_InitStruct.TIM_ClockDivision = TIM_CKD_DIV1;
	//计数模式：咱们选择向上计数
	TIM_InitStruct.TIM_CounterMode = TIM_CounterMode_Up;
	//设置重装载值,计算机会默认+1,决定了PWM波的周期
	TIM_InitStruct.TIM_Period = 999;
	//设置预分频值,计算机会默认+1,计数频率,72MHZ/72=1MHZ
	TIM_InitStruct.TIM_Prescaler = 71;
	//高级定时器需要的参数，这里不进行设置
//	TIM_InitStruct.TIM_RepetitionCounter
	//定时器3,4的初始化
	TIM_TimeBaseInit(TIM3,&TIM_InitStruct);
	TIM_TimeBaseInit(TIM4,&TIM_InitStruct);
	//设置重装载寄存器,避免出现毛刺信号
	TIM_ARRPreloadConfig(TIM3,ENABLE);
	TIM_ARRPreloadConfig(TIM4,ENABLE);
	//定义一个比较结构体，并初始化
	TIM_OCInitTypeDef TIM_OCInitStruct = {0};
	//PWM波的模式，设置低于比较值的为有效电平
	TIM_OCInitStruct.TIM_OCMode = TIM_OCMode_PWM1;
	//PWM波的极性,有效电平为高电平
	TIM_OCInitStruct.TIM_OCPolarity = TIM_OCPolarity_High;
	//输出使能
	TIM_OCInitStruct.TIM_OutputState = TIM_OutputState_Enable;
	//设置比较值
	TIM_OCInitStruct.TIM_Pulse = 0;
	//初始化定时器的输出通道
	TIM_OC1Init(TIM3,&TIM_OCInitStruct);
	TIM_OC2Init(TIM3,&TIM_OCInitStruct);
	TIM_OC3Init(TIM3,&TIM_OCInitStruct);
	TIM_OC4Init(TIM3,&TIM_OCInitStruct);
	//使能定时器通道的比较值:改变占空比更丝滑
	TIM_OC1PreloadConfig(TIM3,TIM_OCPreload_Enable);
	TIM_OC2PreloadConfig(TIM3,TIM_OCPreload_Enable);
	TIM_OC3PreloadConfig(TIM3,TIM_OCPreload_Enable);
	TIM_OC4PreloadConfig(TIM3,TIM_OCPreload_Enable);
	//初始化定时器的输出通道
	TIM_OC1Init(TIM4,&TIM_OCInitStruct);
	TIM_OC2Init(TIM4,&TIM_OCInitStruct);
	TIM_OC3Init(TIM4,&TIM_OCInitStruct);
	TIM_OC4Init(TIM4,&TIM_OCInitStruct);
	//使能定时器通道的比较值:改变占空比更丝滑
	TIM_OC1PreloadConfig(TIM4,TIM_OCPreload_Enable);
	TIM_OC2PreloadConfig(TIM4,TIM_OCPreload_Enable);
	TIM_OC3PreloadConfig(TIM4,TIM_OCPreload_Enable);
	TIM_OC4PreloadConfig(TIM4,TIM_OCPreload_Enable);
	//使能定时器
	TIM_Cmd(TIM3,ENABLE);
	TIM_Cmd(TIM4,ENABLE);
}
//小车的前进
void CAR_Forward(uint16_t speed)
{
	Motor_Left_Fr_F(speed);
	Motor_Right_Back_F(speed);
	Motor_Left_Back_F(speed);
	Motor_Right_Fr_F(speed);
}
//小车的后退
void CAR_Back(uint16_t speed)
{
	Motor_Left_Fr_B(speed);
	Motor_Right_Back_B(speed);
	Motor_Left_Back_B(speed);
	Motor_Right_Fr_B(speed);
}
//差速右转大弯
void Car_Right_Big(uint16_t speed)
{
	Motor_Left_Fr_F(speed);
	Motor_Right_Back_F(speed-200);
	Motor_Left_Back_F(speed);
	Motor_Right_Fr_F(speed-200);
}
//右转中弯
void Car_Right_Mid(uint16_t speed)
{
	Motor_Left_Fr_F(speed);
	Motor_Right_Back_F(0);
	Motor_Left_Back_F(speed);
	Motor_Right_Fr_F(0);
}
//右转小弯
void Car_Right_Small(uint16_t speed)
{
	Motor_Left_Fr_F(speed);
	Motor_Left_Back_F(speed);
	Motor_Right_Fr_B(speed);
	Motor_Right_Back_B(speed);
}
//停止
void Car_Stop(void)
{
	Motor_Left_Fr_F(0);
	Motor_Right_Back_F(0);
	Motor_Left_Back_F(0);
	Motor_Right_Fr_F(0);
}

//差速左转大弯
void Car_Left_Big(uint16_t speed)
{
	Motor_Left_Fr_F(speed-200);
	Motor_Right_Back_F(speed);
	Motor_Left_Back_F(speed-200);
	Motor_Right_Fr_F(speed);
}
//左转中弯
void Car_Left_Mid(uint16_t speed)
{
	Motor_Left_Fr_F(0);
	Motor_Right_Back_F(speed);
	Motor_Left_Back_F(0);
	Motor_Right_Fr_F(speed);
}
//左转小弯
void Car_Left_Small(uint16_t speed)
{
	Motor_Right_Back_F(speed);
	Motor_Right_Fr_F(speed);
	Motor_Left_Fr_B(speed);
	Motor_Left_Back_B(speed);
}



