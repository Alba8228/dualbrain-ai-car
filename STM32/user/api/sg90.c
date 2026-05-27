#include "sg90.h"
/*
 **********************************************
 以下程序是舵机控制程序
 ***********************************************/
int steer1Angle = 0, steer2Angle = -90;
void Tim1_SteerInit(u16 psc, u16 arr, u16 ccr)
{
	GPIO_InitTypeDef GPIO_InitStructure={0};
	TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
	TIM_OCInitTypeDef TIM_OCInitStructure={0};
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_TIM1, ENABLE);
	
	// 输出比较通道 GPIO 初始化
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8 | GPIO_Pin_11;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructure);
	
	/**********************定时器初始化************************/
	TIM_TimeBaseStructure.TIM_Period = arr - 1;// 自动重装载寄存器的值
	TIM_TimeBaseStructure.TIM_Prescaler = psc - 1;// 驱动 CNT 计数器的时钟
	TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;// 时钟分频因子 ，配置死区时间时需要用到
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;// 计数器计数模式，设置为向上计数
	TIM_TimeBaseStructure.TIM_RepetitionCounter = 0;// 重复计数器的值
	TIM_TimeBaseInit(TIM1, &TIM_TimeBaseStructure);
	TIM_ARRPreloadConfig(TIM1, ENABLE);

	TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;// 配置为 PWM 模式 1
	TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;// 输出使能
	TIM_OCInitStructure.TIM_OutputNState = TIM_OutputNState_Disable;// 互补输出使能
	TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;// 输出通道电平极性配置
	TIM_OCInitStructure.TIM_OCNPolarity = TIM_OCNPolarity_High;// 互补输出通道电平极性配置
	TIM_OCInitStructure.TIM_OCIdleState = TIM_OCIdleState_Set;// 输出通道空闲电平极性配置
	TIM_OCInitStructure.TIM_OCNIdleState = TIM_OCNIdleState_Reset;// 互补输出通道空闲电平极性配置
	TIM_OCInitStructure.TIM_Pulse = (steer1Angle*(2000.0/180)+1500);// 设置占空比大小
	
	TIM_OC1Init(TIM1, &TIM_OCInitStructure);
	TIM_OC1PreloadConfig(TIM1, TIM_OCPreload_Enable);
	
	TIM_OCInitStructure.TIM_Pulse = (steer2Angle*(-2000.0/180)+500);
	TIM_OC4Init(TIM1, &TIM_OCInitStructure);
	TIM_OC4PreloadConfig(TIM1, TIM_OCPreload_Enable);
	
	TIM_ITConfig(TIM1, TIM_IT_Update, DISABLE);
	NVIC_DisableIRQ(TIM1_UP_IRQn);
	
	// 使能计数器
	TIM_Cmd(TIM1, ENABLE);
	// 主输出使能
	TIM_CtrlPWMOutputs(TIM1, ENABLE);	
}


void Steer_Init(void)
{
	Tim1_SteerInit(72, 20000, 1500);
	Steer_SetAngle(1, steer1Angle);
	Steer_SetAngle(2, steer2Angle);
}

void Steer_SetPWM(uint8_t steer, uint16_t pwm) 
{
	switch(steer)
	{
		case 1: TIM_SetCompare1(TIM1, pwm); break;
		case 2: TIM_SetCompare4(TIM1, pwm); break;
	}
}

/*************************************************
 *Steer1:	 可控范围：-90° -- 90°
 *	500-2500	0°对应1500	-90°对应500	90°对应2500
 *
 *Steer2:  可控范围：0° -- -180°
 *	500-2500	0°对应500	 -180°对应2500
 *************************************************
 */
void Steer_SetAngle(uint8_t steer, int angle) 
{
	switch(steer)
	{
		case 1: 
			if(angle < -90 || angle > 90)	break;
			angle = angle*(2000.0/180)+1500;
			TIM_SetCompare1(TIM1, angle); 
		break;
		case 2: 
			if(angle < -180 || angle > 0)	break;
			angle = angle*(-2000.0/180)+500;
			TIM_SetCompare4(TIM1, angle); 
		break;
	}
}

uint8_t SteerDir;
void Steer_Control(void)//30ms调用一次，固定周期调用，用于匀速控制舵机转动
{
	switch(SteerDir) {//这个方向的变量，由蓝牙、WIFI可以控制改变
		case SteerStop:  break;
		case SteerLeft: steer1Angle+=2; break;
		case SteerRight: steer1Angle-=2; break;
		case SteerUp: steer2Angle+=2; break;
		case SteerDown: steer2Angle-=2; break;
		default:break;
	}
	steer1Angle = steer1Angle>90?90:(steer1Angle<-90?(-90):steer1Angle);  // 限幅
	steer2Angle = steer2Angle>0?0:(steer2Angle<-180?(-180):steer2Angle); 	// 限幅
	Steer_SetAngle(1, steer1Angle);
	Steer_SetAngle(2, steer2Angle);
}




