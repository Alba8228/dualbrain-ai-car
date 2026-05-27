#include "delay.h"

uint16_t key_num = 0;
uint16_t beep_flag =0;
uint16_t beep_num =0;
uint16_t sg90_num =0;
//系统滴答定时器的中断函数
//1ms
void SysTick_Handler(void)
{
   key_num ++;
   sg90_num ++;
	if(beep_flag ==1)
	{
		beep_num ++;
	}
}




//系统定时器初始化
void Systick_Init(uint32_t load)
{
	if(SysTick_Config(load) == 1)
	{
		while(1);
	}
}


void Delay_us(uint32_t time)
{
	while(time--) {
		delay_1us();
	}
}

void Delay_ms(uint32_t time)
{
	uint64_t t = time*1000;
	while(t--) {
		delay_1us();
	}
}






