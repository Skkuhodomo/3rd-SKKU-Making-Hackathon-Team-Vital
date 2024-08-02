import firebase_admin
from firebase_admin import credentials, db
import requests
import os
import replicate
from openai import OpenAI
import threading
import pygame

client = OpenAI()

# OpenAI API 키 설정
client.api_key = "openai-api-key" 
replicate.api_key = "replicate-api-key"


cred = credentials.Certificate('./certifiaction/auth.json')
# Firebase Admin SDK 초기화
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://minit-cbcef-default-rtdb.firebaseio.com'
})
"""데이터를 가져오기 """
# get_sensor_data 함수는 firebase의 실시간 데이터베이스에서 센서 데이터를 가져옵니다.
def get_sensor_data():
    sensor_data = {}
    ref = db.reference('/')
    sensor_data['user_satistify'] = ref.child('user_satistify').get()
    sensor_data['im_home_now'] = ref.child('im_home_now').get()
    sensor_data['temp'] = ref.child('temp').get()
    sensor_data['HRV'] = ref.child('HRV').get()
    sensor_data['humid'] = ref.child('humid').get()
    return sensor_data
# get_user_needs 함수는 firebase의 실시간 데이터베이스에서 사용자의 요구사항을 가져옵니다.
def get_user_needs():
    user_needs = {}
    ref = db.reference('/')
    user_needs['user_satistify'] = ref.child('user_satistify').get()
    return user_needs

"""gpt를 통해 프롬프트와 설명을 생성하는 함수"""
# 신체 상태에 따라 적절한 프롬프트를 GPT-4o에게 넣어주기 위한 것입니다.
def get_pulse_music_recommendation(pulse: int):
    if pulse < 80:
        return "Suggest calm and relaxing music to maintain a peaceful environment."
    elif 80 <= pulse < 100:
        return "Suggest moderately upbeat and energetic music to match the heightened state."
    else:
        return "Suggest soothing and relaxing music to help reduce stress levels."

def get_temperature_music_recommendation(body_temperature : int):
    if body_temperature < 35.5:
        return "Suggest warm and comforting music to create a cozy atmosphere."
    elif 35.5 <= body_temperature < 37.5:
        return "Suggest balanced and neutral music to maintain equilibrium."
    else:
        return "Suggest classic music and natural sounds like water and wind."
# 환경 상태에 따라 적절한 프롬프트를 GPT-4o에게 넣어주기 위한 것입니다. 
def get_light_music_recommendation(light: int ):
    if light < 300:  # 어두움
        return "Suggest calm and relaxing music for a dimly lit environment."
    elif 300 <= light < 800:  # 적당한 밝기
        return "Suggest upbeat and positive music for a well-lit space."
    else:  # 밝음
        return "Suggest energetic and lively music for a bright environment."

def get_humidity_music_recommendation(humidity: int):
    if humidity < 40:  # 건조
        return "Suggest calming music with natural sounds like rain or flowing water."
    elif 40 <= humidity < 60:  # 적절
        return "Suggest a diverse range of music suitable for a comfortable humidity level."
    else:  # 습함
        return "Suggest upbeat and refreshing music to counter the humidity."

    
# 파인튜닝 없이 프롬프트 엔지니어링을 통해 충분히 니즈를 만족시키는 결과물을 얻었습니다. 
# 프롬프트는 자유롭게 수정하셔도 좋습니다.
def generate_prompt(sensor_data: dict, user_needs: dict ):
    prompt = f"""
    You are a helpful AI assistant that suggests actions based on sensor data and user needs.
    You are a good assistant. You generate prompts needed for an MusicGen that creates appropriate music based on user's sensor data and user's needs.
    You must use ENGLISH!!
    Here is the sensor data:
    - Humidity: {sensor_data.get('humid')}
    - Pulse: {sensor_data.get('HRV')}
    - Body Temperature: {sensor_data.get('temp')}

    You need to write a prompt to generate music suitable for body temperature, and humidity values and Pulse. 
    The user's state based on pulse rate is categorized as follows, and the appropriate type of music for each case is:

    Given the user's pulse rate is {sensor_data.get('HRV')} bpm:
    {get_pulse_music_recommendation(sensor_data.get('HRV'))}

    Given the user's body temperature is {sensor_data.get('temp')}°C:
    {get_temperature_music_recommendation(sensor_data.get('temp'))}
    Here are the user needs:
    - {user_needs.get('user_satistify')}

    Based on this information, suggest some actions the user could take.

    Example prompt (
      sensor_data_example = (
    'humid': 45,
    'HRV': 110,
    'temp': 37
     )
    : Create soothing music with gentle bird and water sounds that helps induce a state of relaxation. with cool like wind sounds.
    """
    return prompt

# 응답을 생성하는 함수입니다.(중요)
def generate_response(prompt: str):
  response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # Or use a different GPT model
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": "generate prompt for musicGen json 타입이고, prompt, description을 반환해주세요.decription은 음악이 재생되기 전에, 사용자의 현재 상태에 대하여 친절히 설명하고, 당신이 만들 음악에 대한 자세한 설명을 해줘. 한국어로 "},
      ],
    response_format = {'type':"json_object"}
  )
  return response.choices[0].message.content["prompt"], response.choices[0].message.content["description"]
"""생성된 설명을 음성으로 변환하는 곳입니다."""
def description_to_voice(description: str):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input= description,
    )
    response.stream_to_file("./output/music_description.mp3")


"""음악을 생성하는 함수 """
def generate_music(prompt):
  inputs = {
    'prompt': prompt,
    "model_version": "stereo-large",
    "output_format": "mp3",
    "normalization_strategy": "peak",
    "duration" : 20, # 20초의 음악을 반복해서 재생하면 시간 절약이 됩니다. 
  }
  output = replicate.run(
  "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
  input=inputs
  )
  return output

"""이벤트 발생을 감지하여 생성하는 함수 """



# 이벤트 발생을 감지하여 생성하는 함수
def listener(event):
    if event.data == 1:
        sensor_data = get_sensor_data()
        user_data = get_user_needs()
        print(sensor_data, "sensor_data")
        print(user_data, "user_data")

        prompt = generate_prompt(sensor_data, user_data)
        music_prompt, description = generate_response(prompt)
        
        description_to_voice(description)
        
        def play_description():
            pygame.mixer.music.load("output/music_description.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        
        def create_and_play_music():
            music = generate_music(music_prompt)
            response = requests.get(music)
            if response.status_code == 200:
                with open('output/music.mp3', 'wb') as f:
                    f.write(response.content)
                pygame.mixer.music.load("output/music.mp3")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

        description_thread = threading.Thread(target=play_description)
        music_thread = threading.Thread(target=create_and_play_music)
        
        description_thread.start()
        music_thread.start()
        
        description_thread.join()
        music_thread.join()


def main():
    ref = db.reference('/music_create') #파이어베이스에 리스너 설정 
    ref.listen(listener)

if __name__ == '__main__':
    main()
