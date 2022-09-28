from time import sleep, time
import pytube
import spotipy
from tabulate import tabulate
from spotipy.oauth2 import SpotifyClientCredentials
import os
import youtubesearchpython as ytsearch
from mutagen.mp4 import MP4


print("Logging into Spotify...", end=' ')

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    "914307bab744408595602cf269ec892c", "4dd6a891d3b94e2f93a68734d5ded526"))
print("Done")

dir = os.path.dirname(os.path.realpath(__file__))

subdir = ''


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    pct_completed = bytes_downloaded / total_size * 100
    print(f"{round(pct_completed, 0)}%", end='\t')


def getUrlType(url):
    url = str(url)
    url = url.split('/')
    type = url[-2]

    url.remove('')

    if 'http' not in url[0] or 'https' not in url[0]:
        return False

    if type == 'playlist':
        return 'sp_playlist'
    if type == 'album':
        return 'sp_album'
    if type == 'track':
        return 'sp_track'
    if 'youtube' in url[1]:
        return 'yt_track'

    return False


def normalize(title):
    title = str(title)
    forbidden_chars = ['"', "'", '?', '|', '/', '\\', '*', ':', '<', '>']
    for char in forbidden_chars:
        title = title.replace(char, '')
    return title


def yt_download(url, urlType=None):
    if urlType == None:
        urlType = getUrlType(url)

    ytVideo = pytube.YouTube(url, on_progress_callback=on_progress)

    downdir = dir+'/ex'
    # itag 139 abr="48kbs" low quality
    # ->itag 140<- abr="128kbs" higher quality

    print(f"{ytVideo.title}\tdownloading", end='\t')

    if os.path.exists(f"{downdir}/{normalize(ytVideo.title)}.mp4") == False:
        try:
            ytVideo.streams.get_audio_only(subtype="mp4").download(
                downdir, filename=f"{normalize(ytVideo.title)}.mp4", skip_existing=True)
        except:
            print('Error', end='\t')
    
    attachMetadata(f"{downdir}/{normalize(ytVideo.title)}.mp4", ytVideo)
    print('\n', end='')
    print('Done')


def sp_download(url, urlType=None):
    if urlType == None:
        urlType = getUrlType(url)

    # print(f"{urlType} URL detected")
    print("Fetching...")

    videosToSearch = []

    if urlType == 'sp_playlist':
        print(f"Spotify playlist URL detected")

        playlist = spotify.playlist(url)

        print(
            f"playlist '{playlist['name']}' by {playlist['owner']['display_name']} found")
        subdir = f"/{playlist['name']}"

        tracks = playlist['tracks']['items']
        results = playlist['tracks']

        # fetches all tracks
        while results['next']:
            results = spotify.next(results)
            tracks.extend(results['items'])

        for track in tracks:
            if 'track' in track:
                track = track['track']

            # print(f"{track['name']} {track['artists'][0]['name']}")
            videosToSearch.append(
                {'name': track['name'], 'author': track['artists'][0]['name'], 'album':track['album']['name']})

    elif urlType == 'sp_album':
        print(f"Spotify album URL detected")

        album = spotify.album(url)

        print(
            f"album '{album['name']}' by {album['artists'][0]['name']} found")

        subdir = f"/{album['name']}"

        tracks = album['tracks']['items']
        results = album['tracks']

        while results['next']:
            results = spotify.next(results)
            tracks.extend(results['items'])

        for track in tracks:
            if 'track' in track:
                track = track['track']
            # print(f"{track['name']} {track['artists'][0]['name']}")
            videosToSearch.append(
                {'name': track['name'], 'author': track['artists'][0]['name'], 'album': album['name']})

        # print(tabulate(videosToSearch, headers="keys", tablefmt="pretty"))

    elif urlType == 'sp_track':
        print(f"Spotify track URL detected")

        subdir = ''
        track = spotify.track(url)
        # print(track)
        videosToSearch.append(
            {'name': track['name'], 'author': track['artists'][0]['name'], 'album': track['album']['name']})

    downdir = dir+'/ex'+subdir

    print('Track list:')

    print(tabulate(videosToSearch, headers="keys", tablefmt="pretty"))

    sleep(1)

    print("Searching on YT...")
    totalVideos = len(videosToSearch)
    i = 1
    for video in videosToSearch:
        print(f"{i} of {totalVideos}: {video['name']} by {video['author']}", end="\t")
        i += 1
        # ytVideo = pytube.Search(video['name'] +' '+ video['author']).results[0]
        searchError = False
        try:
            sres = ytsearch.VideosSearch(
                f"{video['name']} {video['author']} Official Audio", limit=1, region='IT', timeout=10).result()['result'][0]
        except:
            # print('Connection Error', end='\t')
            # sres = ytsearch.VideosSearch(f"{video['name']} {video['author']}", limit=1, region='IT').result()['result'][0]
            searchError = True
        c = 1
        while searchError == True:
            print(f"attempt {c}", end='\r')
            try:
                sres = ytsearch.VideosSearch(
                    f"{video['name']} {video['author']}", limit=1, region='IT').result()['result'][0]
                searchError = False
            except:
                c += 1

        ytVideo = pytube.YouTube(
            sres['link'], on_progress_callback=on_progress, on_complete_callback=print("Done", end='\t'))

        # itag 139 abr="48kbs" low quality
        # ->itag 140<- abr="128kbs" higher quality

        # print(f"downloading", end='\t')

        if os.path.exists(f"{downdir}/{normalize(video['name'])}.mp4") == False:
            try:
                ytVideo.streams.get_audio_only(subtype="mp4").download(
                    downdir, filename=f"{normalize(video['name'])}.mp4", skip_existing=True)
            except:
                print('Error', end='\t')

        attachMetadata(f"{downdir}/{normalize(video['name'])}.mp4", video)
        print('\n', end='')
        # print('Done')

def attachMetadata(file, metadata):
    # metadata=dict()
    metadata = metadata.__dict__
    f = MP4(file)
    tagmap = dict({
    "author" :"\xa9ART",
    "name":"\xa9nam",
    "title":"\xa9nam",
    "album":"\xa9alb",
    "genre":"\xa9gen"})

    for key in metadata.keys():
        if metadata[key] is not None and key in tagmap.keys():
            f[tagmap[key]] = metadata[key]
    
    f.save()


def main(urls = None):
    # check input file
    if str(input("Input from file y/n: ")) == 'y':

        if os.path.exists('input.txt'):
            with open("input.txt", 'r') as file:
                urls = []
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('#') or line.startswith('\n') or len(line) == 0:
                        # ignore lines with #
                        continue
                    else:
                        arg = line.split(' ')[0]
                        urls.append(arg)
                        line = file.readline()
                
                file.close()
        else:
            print(f"input.txt not found in {dir}")
            print("Please use manual input")

    if urls is None or len(urls) == 0:
        urls = str(input("Insert spotify or youtube url(s): ")).split(' ')
    print(urls)
    # getopt.getopt(sys.argv[1:], )

    for url in urls:
        urlType = getUrlType(url)
        if urlType:
            platform = urlType.split('_')[0]
            if platform == 'sp':
                sp_download(url, urlType=urlType)
            if platform == 'yt':
                yt_download(url, urlType=urlType)
        else:
            print(f"{url} is not a url")


if __name__ == "__main__":
    print("File executed as main")
    main()
