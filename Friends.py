import sys
import urllib.error
from urllib import request
import random
import pickle
import re
import os
import tkinter as tk
from tkinter import PhotoImage
from bs4 import BeautifulSoup
from difflib import get_close_matches
import webbrowser

sys.setrecursionlimit(500)

# Define the list of extra stopwords
extra_stopwords = ["'d", "i-", "i-i", "i'll", "'ll", "'ve", "'", "'re", "'m", "okay", "oh...", "oh", "hey", "gotta", "would", "won't", "'m", "'s", "oh", "n't", "...", "--", "that's"]

# Define the set of stopwords
stop_words = set(["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"] + extra_stopwords)

# Define the series and doubleepisode lists
series = [
    (1, 24),
    (2, 24),
    (3, 25),
    (4, 23),
    (5, 23),
    (6, 24),
    (7, 23),
    (8, 23),
    (9, 23),
    (10, 17),
]
doubleepisode = ["0212", "0615", "0923", "1017"]

# Define dictionaries to store transcripts, tokens, and titles
transcripts = {}
tokens = {}
titles = {}

def custom_tokenize(text):
    # Custom tokenizer to split words based on spaces and punctuation
    return re.findall(r'\b\w+\b', text.lower())

def load_transcripts_tokens_titles():
    global transcripts, tokens, titles
    for serie, episodes in series:
        punctuation = '''!()[]:"\,<>./...?'''
        transcripts[serie] = {}
        tokens[serie] = {}
        titles[serie] = {}
        for episode in range(1, episodes + 1):
            if "{serie:02d}{episode:02d}".format(serie=serie, episode=episode) in doubleepisode:
                url = "https://fangj.github.io/friends/season/{serie:02d}{episode_1:02d}-{serie:02d}{episode_2:02d}.html".format(
                    serie=serie, episode_1=episode, episode_2=episode + 1
                )
            else:
                url = "https://fangj.github.io/friends/season/{serie:02d}{episode:02d}.html".format(serie=serie, episode=episode)

            try:
                html = request.urlopen(url).read()
            except urllib.error.HTTPError:
                print("Could not get series {} episode {}".format(serie, episode))
                continue
            title = str(BeautifulSoup(html, 'html.parser').title.string)
            raw = BeautifulSoup(html, 'html.parser').body

            transcripts[serie][episode] = raw.get_text()
            titles[serie][episode] = title

            tokens_raw = custom_tokenize(transcripts[serie][episode])
            tokens_no_punct = [item for item in tokens_raw if item not in punctuation]
            tokens_list = [word for word in tokens_no_punct if word not in stop_words]
            tokens[serie][episode] = tokens_list

def find_matching_video(keyword):
    # Check both "Videos" and "videos" folders
    video_folders = ["Videos", "videos"]
    for video_folder in video_folders:
        if os.path.exists(video_folder):
            video_files = os.listdir(video_folder)
            keyword_parts = keyword.split('_')

            def video_matches_parts(file_parts):
                return all(part.lower() in file_parts for part in keyword_parts)

            matching_videos = [filename for filename in video_files if video_matches_parts(filename.lower().split('_'))]
            if matching_videos:
                return os.path.join(video_folder, random.choice(matching_videos))

            # If exact match not found, find closest match using Levenshtein distance
            closest_match = get_close_matches(keyword, video_files, n=1)
            if closest_match:
                return os.path.join(video_folder, closest_match[0])

    return None

def generate_random_episode(keyword):
    keyword_count = {}
    for serie_number, serie in tokens.items():
        for episode_number, episode in serie.items():
            for word in episode:
                if keyword == word:
                    try:
                        keyword_count[serie_number, episode_number] += 1
                    except:
                        keyword_count[serie_number, episode_number] = 1
    sorted_count = sorted(keyword_count, key=keyword_count.get, reverse=True)[:5]
    final_dict = {}
    for serie_number, serie in sorted_count:
        final_dict[serie_number, serie] = titles[serie_number][serie]
    random_episode = random.choice(list(final_dict.items()))
    return str(random_episode[0]) + ': ' + random_episode[1]

def generate_episode_script_with_video(keyword):
    selected_episode = generate_random_episode(keyword)
    video_link = find_matching_video(keyword)

    print("Selected Episode:", selected_episode)

    if video_link:
        print("Playing video:", video_link)
    else:
        print("No video available for this keyword/sentence.")
        print("Playing the closest matching video instead.")
        closest_video = find_matching_video(get_close_matches(keyword, tokens[1][1])[0])
        if closest_video:
            print("Playing closest video:", closest_video)

    # Generate the script with location and character information
    episode_number, episode_title = selected_episode.split(': ')
    script = transcripts[int(episode_number)][int(episode_title)]
    script_lines = script.split('\n')

    def get_location_character_info(script_line):
        location_info = re.search(r'\*Location:\s*(.*?)\*', script_line)
        character_info = re.search(r'\*([^*]+)\*', script_line)
        return location_info.group(1) if location_info else None, character_info.group(1) if character_info else None

    current_location, current_character = None, None
    for line in script_lines:
        location_info, character_info = get_location_character_info(line)
        if location_info:
            current_location = location_info
        if character_info:
            current_character = character_info
        if current_location and current_character:
            print(f"Scene: Location - {current_location}, Character/Action - {current_character}")
            print(f"Playing video clip for: Location - {current_location}, Character/Action - {current_character}")

            video_clip_path = video_link
            if not video_clip_path:
                print("No video available for this keyword/sentence.")
                print("Playing the closest matching video instead.")
                closest_video = find_matching_video(get_close_matches(current_location, tokens[1][1])[0])
                if closest_video:
                    video_clip_path = closest_video

            if video_clip_path:
                play_video_clip(video_clip_path, line)
            else:
                print("No video available for this scene.")

            current_location, current_character = None, None

        print(line)

def play_video_clip(video_path, script_line):
    # Replace this function with code for displaying video thumbnails
    # For demonstration, we'll just use an image of a video player
    root = tk.Tk()
    root.title("Video Player")
    root.geometry("800x600")

    canvas = tk.Canvas(root, width=800, height=450)
    canvas.pack()

    video_player_image = PhotoImage(file="video_player_image.png")  # Replace this with the actual image path
    canvas.create_image(0, 0, anchor=tk.NW, image=video_player_image)

    subtitles = tk.Label(root, text="", anchor="w", font=("Arial", 16))
    subtitles.pack(side=tk.BOTTOM, fill=tk.X)
    subtitles.config(text=script_line)

    def open_video(event):
        webbrowser.open(video_path)

    canvas.bind("<Button-1>", open_video)

    root.mainloop()

if __name__ == '__main__':
    load_transcripts_tokens_titles()
    keyword = input("Enter a keyword: ")
    generate_episode_script_with_video(keyword)
