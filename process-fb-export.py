from base64 import encode
import os
import shutil

for folder in os.listdir("inbox"):
    chat_name = folder.split("_")[0]
    print(chat_name)

    src = "inbox/" + folder + "/message_1.json"
    dst = "fb/" + chat_name + ".json"

    shutil.copy(src, dst)