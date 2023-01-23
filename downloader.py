import os
from argparse import ArgumentParser, RawTextHelpFormatter
# from warnings import warn

title = '''
       /$$                                   /$$                          /$$                                       
      | $$                                  | $$                         | $$                                       
  /$$$$$$$  /$$$$$$  /$$  /$$  /$$ /$$$$$$$ | $$  /$$$$$$  /$$$$$$   /$$$$$$$  /$$$$$$   /$$$$$$  /$$$$$$  /$$   /$$
 /$$__  $$ /$$__  $$| $$ | $$ | $$| $$__  $$| $$ /$$__  $$|____  $$ /$$__  $$ /$$__  $$ /$$__  $$/$$__  $$| $$  | $$
| $$  | $$| $$  \ $$| $$ | $$ | $$| $$  \ $$| $$| $$  \ $$ /$$$$$$$| $$  | $$| $$$$$$$$| $$  \__/ $$  \ $$| $$  | $$
| $$  | $$| $$  | $$| $$ | $$ | $$| $$  | $$| $$| $$  | $$/$$__  $$| $$  | $$| $$_____/| $$     | $$  | $$| $$  | $$
|  $$$$$$$|  $$$$$$/|  $$$$$/$$$$/| $$  | $$| $$|  $$$$$$/  $$$$$$$|  $$$$$$$|  $$$$$$$| $$/$$  | $$$$$$$/|  $$$$$$$
 \_______/ \______/  \_____/\___/ |__/  |__/|__/ \______/ \_______/ \_______/ \_______/|__/__/  | $$____/  \____  $$
                                                                                                | $$       /$$  | $$
                                                                                                | $$      |  $$$$$$/
                                                                                                |__/       \______/ 

Author: dragonero2704
Github: https://github.com/dragonero2704/Spotify-Downloader
Version: 2
'''

dir = os.path.dirname(os.path.realpath(__file__))
# check dependencies
if os.name == "posix":
    inst = "sudo pip install {}"
elif os.name == "nt":
    inst = "pip install {}"

print("Checking dependencies")
print("[If something is missing I will install it for you!]")

try:
    from termcolor import cprint
except:
    print("Missing termcolor")
    os.system(inst.format("termcolor"))
    from termcolor import cprint

try:
    import colorama
except:
    os.system(inst.format("colorama"))
    import colorama
finally:
    if os.name == "nt":
        colorama.init()

try:
    import pytube
except:
    cprint("Missing pytube", "yellow")
    os.system(inst.format("pytube"))
    import pytube

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except:
    cprint("Missing spotipy", "yellow")
    os.system(inst.format("spotipy"))
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials


try:
    from tabulate import tabulate
except:
    cprint("Missing tabulate", "yellow")
    os.system(inst.format("tabulate"))
    from tabulate import tabulate


try:
    from mutagen.mp4 import MP4
except:
    cprint("Missing mutagen", "yellow")
    os.system(inst.format("mutagen"))
    from mutagen.mp4 import MP4


try:
    import youtubesearchpython as ytsearch
except:
    cprint("Missing youtubesearchpython", "yellow")
    os.system(inst.format("youtubesearchpython"))
    import youtubesearchpython as ytsearch

try:
    import json
except:
    cprint("Missing json", "yellow")
    os.system(inst.format("json"))
    import json

try:
    import dotenv
except:
    cprint("Missing python-dotenv", "yellow")
    os.system(inst.format("python-dotenv"))
    import dotenv

cprint("Dependencies: ok", "green")
pathToEnv = dotenv.find_dotenv()
if pathToEnv != '':
    dotenv.load_dotenv(pathToEnv)
    spotifyClientId = os.getenv('spotifyClientId')
    spotifySecret = os.getenv('spotifySecret')
elif os.path.exists("./config.json"):
    config = json.load(open("config.json"))
    spotifyClientId = config['spotifyClientId']
    spotifySecret = config['spotifySecret']
else:
    cprint("Warning: .env or config.json not found for spotify credentials", "yellow")
# config = json.load(open("config.json"))
# print(config)
cprint("Logging into Spotify:", "blue", end=" ")
try:
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    spotifyClientId, spotifySecret))
except:
    cprint("failed", "red")
    spotify = False
else:
    cprint("success", "green")


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    pct_completed = bytes_downloaded / total_size * 100
    print(f"{round(pct_completed, 0)}%", end='\t')

def getUrlType(url):
    if url.startswith("http") == False and url.startswith("https") == False:
        raise Exception(f"Invalid link: {url}")

    url = str(url)
    url = url.split('/')
    url.remove('')
    type = url[-2]
    
    if type == 'playlist':
        return 'sp_playlist'
    if type == 'album':
        return 'sp_album'
    if type == 'track':
        return 'sp_track'
    if 'youtube' in url[1]:
        return 'yt_track'

    raise Exception(f"Invalid link: {url}")


def normalize(title):
    title = str(title)
    forbidden_chars = ['"', "'", '?', '|', '/', '\\', '*', ':', '<', '>']
    for char in forbidden_chars:
        title = title.replace(char, '')
    return title


def yt_download(url,args, urlType=None):
    if urlType == None:
        urlType = getUrlType(url)

    ytVideo = pytube.YouTube(url, on_progress_callback=on_progress)
    downdir = dir+'/ex'
    if args.output:
        downdir = args.output
    # itag 139 abr="48kbs" low quality
    # ->itag 140<- abr="128kbs" higher quality
    print(f"{ytVideo.title}\tdownloading", end='\t')

    if os.path.exists(f"{downdir}/{normalize(ytVideo.title)}.mp4") == False:
        try:
            ytVideo.streams.get_audio_only(subtype="mp4").download(
                downdir, filename=f"{normalize(ytVideo.title)}.mp4", skip_existing=True)
        except:
            cprint('Error\t', "red")
    
    attachMetadata(f"{downdir}/{normalize(ytVideo.title)}.mp4", ytVideo)
    


def sp_download(url,args, urlType=None):
    if not spotify:
        cprint("Error: Spotify not logged in", "red")
        return

    if urlType == None:
        urlType = getUrlType(url)

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

    if args.output:
        downdir = args.output+subdir
    else:
        downdir = dir+'/ex'+subdir

    print('Track list:')

    print(tabulate(videosToSearch, headers="keys", tablefmt="pretty"))


    cprint("Searching on YT...", "blue", end='')
    totalVideos = len(videosToSearch)
    i = 1
    for video in videosToSearch:
        print(f"\n{i} of {totalVideos}: {video['name']} by {video['author']}", end="\t")
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
            sres['link'], on_progress_callback=on_progress)

        # itag 139 abr="48kbs" low quality
        # ->itag 140<- abr="128kbs" higher quality

        # print(f"downloading", end='\t')

        if os.path.exists(f"{downdir}/{normalize(video['name'])}.mp4") == False:
            try:
                ytVideo.streams.get_audio_only(subtype="mp4").download(
                    downdir, filename=f"{normalize(video['name'])}.mp4", skip_existing=True)
            except Exception as e:
                cprint('Error: {}'.format(e), "red", end='')
            else:
                attachMetadata(f"{downdir}/{normalize(video['name'])}.mp4", video)

        

def attachMetadata(file, metadata):
    
    metadata = metadata.__dict__
    
    f = MP4(file)
    tagmap = {
    "author" :"\xa9ART",
    "name":"\xa9nam",
    "title":"\xa9nam",
    "album":"\xa9alb",
    "genre":"\xa9gen"}

    for key in metadata:
        if metadata[key] is not None and key in tagmap:
            f[tagmap[key]] = metadata[key]
    
    f.save()

def main(urls = None):
    parser = ArgumentParser(
        prog=__file__.split('\\')[-1],
        usage="./%(prog)s -f <inputfile path> -o <outputdirectory> -i <url(s)>",
        formatter_class=RawTextHelpFormatter,
        description=cprint(title, "white", attrs=["bold"]),
    )

    inputopt = parser.add_argument_group("input")
    outputopt = parser.add_argument_group("output")

    inputopt.add_argument('-f', '--file', dest="file", action="store", metavar="<Path to input file>", help="The path to the .txt input file")
    inputopt.add_argument("-l", '--link', '--url', dest="url", action="append", metavar="<url to youtube or spotify track>", help="To input multiple links: -l <url> -l <url>" )
    outputopt.add_argument('-o','--output', dest="output", action="store", metavar="<path to output dir>", default=f'{dir}/ex', help="The path to your output directory. Default is set to './ex'")
    outputopt.add_argument('-ao', '--audio-only', dest="audioOnly", action="store_true", help="If this flag is present, only the audio will be downloaded")

    args = parser.parse_args()

    if args.output:
        if os.path.exists(args.output) == False:
            cprint(f"{args.output} not found", "red")

    if args.file:
    # check input file
        if os.path.exists(args.file):
            with open(args.file, 'r') as file:
                urls = []
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('#') or line.startswith('\n') or len(line) == 0:
                        # ignore lines with #
                        continue
                    else:
                        arg = line.split(' ')
                        urls.extend(arg)
                
                file.close()
        else:
            cprint(f"{args.file} not found", "red")
            exit()
    elif args.url is not None:
        urls = args.url
    else:
        urls = str(input("Insert spotify or youtube url(s): ")).split(' ')

    if urls[0] == '\n':
        cprint("No urls inserted, closing", "red")
        exit()

    for url in urls:
        try:
            urlType = getUrlType(url)
        except Exception as e:
            cprint(e, "red")
            continue
        if urlType:
            platform = urlType.split('_')[0]
            if platform == 'sp':
                sp_download(url, args, urlType=urlType)
            if platform == 'yt':
                yt_download(url, args, urlType=urlType)
        else:
            cprint(f"{url} is not a url", "red")


if __name__ == "__main__":
    main()
