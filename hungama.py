import subprocess
import json
import os
import requests
import re
from mutagen.mp4 import MP4
idRegx = re.compile(r"/(\d+)")
m3u8Regx = re.compile(r"_,(.+),.mp4")
metadataRegx = re.compile(r"videodt = ({[\s\S]+?};)")
headers = {
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'x-requested-with': 'XMLHttpRequest',
}

params = {
    'c': 'common',
    'm': 'get_video_mdn_url',
}

def getm3u8(id):
    data = f'content_id={id}'

    response = requests.post('https://www.hungama.com/index.php', params=params, headers=headers, data=data)
    
    if 'media.hungama.com' in response.text:
        return(response.json()['stream_url'])
    else:
        print("Full video not available")
        exit()



def getMetadata(id):
    response = requests.get(f'https://www.hungama.com/video/_/{id}/')
    metadata = metadataRegx.search(response.text).group(1)[:-1]
    metadata = json.loads(metadata)
    return metadata


def tagger(path, metadata):
    file = MP4(path)
    if metadata['video_name'] != '':
        file['\xa9nam'] = metadata['video_name']
    if metadata['album_name'] != '':
        file['\xa9alb'] = metadata['album_name']
    if metadata['genre'] != '':
        file['\xa9gen'] = metadata['genre']
    if metadata['language'] != '':
        file['----:com.apple.iTunes:Language'] = bytes(metadata['language'], 'UTF-8')
    if metadata['vendor'] != '':
        file['cprt'] = metadata['vendor']
    if metadata['singer_list'] != '':
        file['\xa9ART'] = metadata['singer_list']
    if metadata['artist'] != '':
        file['aART'] = metadata['artist']
    if metadata['release_date'] != '':
        file['----:com.apple.iTunes:Release date'] = bytes(metadata['release_date'][:4]+'-'+metadata['release_date'][4:6]+'-'+metadata['release_date'][6:], 'UTF-8')
    file['rtng'] = [2] if metadata['attribute_censor_rating'] else [0]
    if metadata['musicdirector_list'] != '':
        file['----:com.apple.iTunes:Music directors'] = bytes(metadata['musicdirector_list'], 'UTF-8')
    if metadata['actor_list'] != '':
        file['----:com.apple.iTunes:Actors'] = bytes(metadata['actor_list'], 'UTF-8')
    if metadata['lyricist_list'] != '':
        file['----:com.apple.iTunes:Lyricist'] = bytes(metadata['lyricist_list'], 'UTF-8')
    if metadata['image_path'] != '':
        #download image
        response = requests.get(metadata['image_path'])
        file['covr'] = [response.content]
    file.save()
    return 1


if __name__ == '__main__':
    url = input("Enter the URL: ")
    if not os.path.exists("Downloads"):
        os.makedirs("Downloads")
    id = idRegx.search(url).group(1)
    metadata = getMetadata(id)
    filepath = os.path.join(os.getcwd(), "Downloads", f"{metadata['singer_list']} - {metadata['video_name']} ({metadata['release_date'][:4]}).mp4")
    m3u8 = getm3u8(id)
    if not os.path.exists(filepath):
        print("Downloading...")
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', m3u8, '-c', 'copy', filepath])
    print(filepath)
    tagger(filepath, metadata)
    print("Done")

    



