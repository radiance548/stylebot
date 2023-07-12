This app is an implementation of an AI stylist (a “style” bot) that gives suggestions or recommendations of clothing/fashion choices 
to a user depending on how the user chooses to interact with it. 
One way the user can choose to interact with it is by conversing with it textually and it then generates suggestions based on the user’s input. 
Conversely, the user can also choose to upload an image of themselves to it and it then gives automated recommendations based on the user’s appearance data extracted from that image.

The bot uses the ChatGPT API (specifically the GPT 3.5-Turbo model) for the conversation part of the interaction and the DALL-E 2 API for generating realistic images of the recommended/suggested fashion items. Both APIs were created by OpenAI.

The software was developed in the DataButton IDE online and so cannot be run locally on a machine. To run the code, you would have to add it to a new project on the IDE, upload the image icon files for the UI to the project storage, add on OpenAI API key as a secret to the project (for confidentiality) and configure the project to use the following packages: 

streamlit_chat_media
openai
transformers
torch
tensorflow
accelerate

The image files are included in the project folder and the app code can be found in the bot.py file.
I have included a link to the deployed version of my web app here: https://databutton.com/v/n5jrbj6j

Author: Radiance O. Ngonnase
Copyright © 2023 Radiance O. Ngonnase
