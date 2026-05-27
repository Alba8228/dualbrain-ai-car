#include "track.h"
#include "stdio.h"
#include "motor.h"
#include "string.h"


void TRACK_Config(void)
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);

	GPIO_InitTypeDef MOTOR_InitStruct = {0};
	MOTOR_InitStruct.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	MOTOR_InitStruct.GPIO_Pin = GPIO_Pin_7 | GPIO_Pin_8|GPIO_Pin_9|GPIO_Pin_10|GPIO_Pin_11;
	GPIO_Init(GPIOC,&MOTOR_InitStruct);
}

//循迹函数
void Track_Find_Line(void)
{
	switch(Track_GetValue())
	{
		//全黑&&全白情况
		case 0x00:
		case 0x1F:
			Car_Stop();
			break;
		//左转
		case 0x01://00001
		case 0x03://00011
			Motor_Right_Back_F(550);
			Motor_Right_Fr_F(550);
			Motor_Left_Fr_B(300);
			Motor_Left_Back_B(300);
			break;
		//向左转急弯
		case 0x0F://01111
		case 0x07://00111
			Motor_Right_Back_F(500);
			Motor_Right_Fr_F(500);
			Motor_Left_Fr_B(250);
			Motor_Left_Back_B(250);
			break;
		//向右转一个直角弯
		case 0x18://11000
		case 0X10://10000
			Motor_Left_Fr_F(550);
			Motor_Left_Back_F(550);
			Motor_Right_Fr_B(300);
			Motor_Right_Back_B(300);
			break;
		default :
			CAR_Forward(300);
			break;
	}
}

