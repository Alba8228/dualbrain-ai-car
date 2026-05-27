#include "key.h"
//PA0
void KEY_Config(void)
{
	//开时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);
	//定义结构体初始化
	GPIO_InitTypeDef KEY_InitStruct = {0};
	//模式
	KEY_InitStruct.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	//引脚
	KEY_InitStruct.GPIO_Pin = GPIO_Pin_0;
	GPIO_Init(GPIOA,&KEY_InitStruct);
}

//厂家测试接口
void JTAG_SW_Config(void)
{
	//关闭JTAG接口，开启SW接口--PA15、PB3、PB4可用
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);
	GPIO_PinRemapConfig(GPIO_Remap_SWJ_JTAGDisable, ENABLE);
}


//按键扫描函数
uint8_t Get_Key_Value(void)
{
	static uint16_t count = 0;
	if(KEY == 0)//按键按下
	{
		count++;
	}else if(count > 2)
	{
		count = 0;
		return 1;
	}else
	{
		count = 0;
		return 0;
	}
	return 0;
}