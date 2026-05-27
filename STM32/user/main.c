#include "stm32f10x.h"
#include "delay.h"
#include "led.h"
#include "beep.h"
#include "key.h"
#include "usart1.h"
#include "blue.h"
#include "lcd.h"
#include "motor.h"
#include "track.h"
#include "sr04.h"
#include "sg90.h"
#include "wifi.h"


extern const unsigned char gImage_zz[40960];
extern const unsigned char gImage_lanya[7200];
extern const unsigned char gImage_bizhang[7200];
extern const unsigned char gImage_xunji[7200];
extern const unsigned char gImage_gensui[7200];
extern const unsigned char gImage_wifi[7200];
static uint8_t key_flag  = 0;
static uint8_t key_mode  = 0;

void Key_Shift(void)
{
	if(key_num > 10)
		{
			key_num = 0;
			if(Get_Key_Value() == 1)//按键按下
			{
				key_mode ++;
				beep_flag = 1;
				key_flag =1;
				BEEP_ON(BEEP_Port,BEEP_Pin);
				//if(key_mode > MODE)key_mode = 1;			
			}
		}
}

void Show_TeamName(void)
{
	LCD_Fill(20,80,128,160,PINK);
	
	LCD_ShowString(20,120,(u8*)"14:",WHITE ,BLUE ,16,0);
	LCD_ShowString(20,40,(u8*)"35:",WHITE ,BLUE ,16,0);	
	LCD_ShowString(20,60,(u8*)"23:",WHITE ,BLUE ,16,0);
	LCD_ShowString(20,80,(u8*)"28:",WHITE ,BLUE ,16,0);
	LCD_ShowChinese(70,120,(u8*)"徐玉贵",WHITE,BLUE,16,0);
	LCD_ShowChinese(70,40,(u8*)"王盼",WHITE,BLUE,16,0);
	LCD_ShowChinese(70,60,(u8*)"熊勇祥",WHITE,BLUE,16,0);
	LCD_ShowChinese(70,80,(u8*)"贺祥云",WHITE,BLUE,16,0);
}

void sss(const unsigned char gImage[], u8 *p)
{
	key_flag=0; 
	LCD_Fill(0,0,128,160,WHITE); 
	LCD_ShowPicture(32,32,60,60,gImage);
	LCD_ShowChinese(32,96,p,BLUE,WHITE,16,0);
}	

void main(void)
{
	JTAG_SW_Config();
	Systick_Init(72000);
	LED_Config();
	BEEP_Config();
	KEY_Config();
	USART_Config(9600);
	Blue_Config();
	LCD_Init();
	CAR_Motor_Config();
	Sr04_Init();
	TRACK_Config();
	Steer_Init();
	WIFI_Config();
	Show_TeamName();	
	
	while (1)
	{
				
		Key_Shift();
		switch(key_mode)
		{
			case 1 :if(key_flag)sss(gImage_lanya,(u8*)"蓝牙模式");Blue_Analysis(); break;

			case 2 :if(key_flag)sss(gImage_bizhang,(u8*)"避障模式");GetLength_Sr04(); break;
			
			case 3 :if(key_flag)sss(gImage_xunji,(u8*)"寻迹模式");Track_Find_Line(); break;	
			
			case 4 :if(key_flag)sss(gImage_gensui,(u8*)"跟随模式");WIFI_Analysis();/* AI_Mode */
									if(sg90_num > 10){sg90_num =0;Steer_Control();} break;		
			case 5 :if(key_flag)sss(gImage_wifi,(u8*)"远程模式");WIFI_Analysis(); break;
			
			default :key_mode = 1; continue;
		}
		
		if(beep_num > 100){beep_num = 0; beep_flag = 0; BEEP_OFF(BEEP_Port,BEEP_Pin);}
				  	  
	 }
	  
}






























/*
#define MODE 5

if(key_flag){key_flag=0; LCD_Fill(0,0,128,160,WHITE); LCD_ShowPicture(40,35,48,60,gImage_lanya);
			LCD_ShowChinese(32,96,(u8*)"蓝牙模式",BLUE,WHITE,16,0);}	
			
			Blue_Analysis();
if(key_flag){key_flag=0; LCD_Fill(0,0,128,160,WHITE); LCD_ShowPicture(32,32,60,60,gImage_bizhang);	
				LCD_ShowChinese(32,96,(u8*)"避障模式",BLUE,WHITE,16,0);}
			
		  GetLength_Sr04();

if(key_flag){key_flag=0; LCD_Fill(0,0,128,160,WHITE); LCD_ShowPicture(32,32,60,60,gImage_xunji);
				LCD_ShowChinese(32,96,(u8*)"寻迹模式",BLUE,WHITE,16,0);}
							
			Track_Find_Line();

if(key_flag){key_flag=0;LCD_Fill(0,0,128,160,WHITE);LCD_ShowPicture(32,32,60,60,gImage_gensui);
				LCD_ShowChinese(32,96,(u8*)"跟随模式",BLUE,WHITE,16,0);}
			
		  WIFI_Analysis();

if(key_flag){key_flag=0;LCD_Fill(0,0,128,160,WHITE);LCD_ShowPicture(32,32,60,60,gImage_wifi);			
				LCD_ShowChinese(32,96,(u8*)"远程模式",BLUE,WHITE,16,0);}
			
		    WIFI_Analysis();
			
*/
			