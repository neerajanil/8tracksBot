from BTrees.OOBTree import OOBTree
from discord.voice_client import StreamPlayer
from collections import namedtuple, deque





Song = namedtuple("Song", "player name")

class mix_option:
    def __init__(self):
        self.id = 0
        self.mixid = 0
        self.mixname = ''





class channel_state:
    def __init__(self):
        self.id = 0
        self.mix_options = OOBTree()
        self.song_queue = OOBTree()
        self.song_queue_pos = 0
        self.player: StreamPlayer

    def set_id(self, id: int):
        self.id = id

    def add_option(self, option: mix_option):
        try:
            option_index = self.mix_options.maxKey() + 1
        except ValueError:
            option_index = 0
        mix_option.id = option_index
        print('inserting option: ' + str(option_index))
        self.mix_options.insert(option_index, option)
        return option_index
        
    def clear_options(self):
        self.mix_options.clear()

    def empty_queue(self):
        self.song_queue.clear()
        self.reset_queue_pos()

    def add_queue(self, song: Song):
        try:
            song_index = self.song_queue.maxKey() + 1
        except ValueError:
            song_index = 0
        print('inserting song: ' + str(song_index))
        self.song_queue.insert(song_index, song)
        return song_index

    def current_queue_item(self):
        return self.song_queue[self.song_queue_pos]

    def increment_queue_pos(self):
        self.song_queue_pos = self.song_queue_pos + 1
        

    def reset_queue_pos(self):
        self.song_queue_pos = 0
        
    def has_next_song(self):
        if self.song_queue.maxKey() > self.song_queue_pos:
            return True
        else:
            return False

    def play_next(self):
        if self.current_queue_item().player.error:
            print("bad stuff happened.")
            print(self.current_queue_item().player.error)
        if self.has_next_song():
            self.increment_queue_pos()
            next_song = self.current_queue_item()
            next_player: StreamPlayer = next_song.player
            next_player.start()
        else:
            self.empty_queue()


    def play_now(self):
        current_player: StreamPlayer = self.current_queue_item().player
        print('playing : '+ str(self.song_queue_pos) + ' ' + str(current_player.is_alive()))
        if current_player.is_alive() != True:
            print('starting : '+ str(self.song_queue_pos))
            current_player.start()

    def pause(self):
        current_player: StreamPlayer = self.current_queue_item().player
        current_player.pause()        

    def resume(self):
        current_player: StreamPlayer = self.current_queue_item().player
        current_player.resume()

    def stop(self):
        current_player: StreamPlayer = self.current_queue_item().player
        current_player.stop()

