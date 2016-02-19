# H.264 Baseline Profile level 3.0 "avc1.42001e" or "avc1.66.30"
# Note: Use "avc1.66.30" for compatibility with iOS versions 3.0 to 3.1.2.

# H.264 Baseline Profile level 3.1 "avc1.42001f"

# H.264 Main Profile level 3.0 "avc1.4d001e" or "avc1.77.30"
# Note: Use "avc1.77.30" for compatibility with iOS versions 3.0 to 3.12.

# H.264 Main Profile level 3.1 "avc1.4d001f"
# H.264 Main Profile level 4.0 "avc1.4d0028"
# H.264 High Profile level 3.1 "avc1.64001f"
# H.264 High Profile level 4.0 "avc1.640028"
# H.264 High Profile level 4.1 "avc1.640028"

class M3U8Error(Exception):
    def __init__(self, value):
	self.value = value
    def __str__(self):
	return repr(self.value)    



M3U8_VideoCodecs = { 'baseline' : {'3.0': 'avc1.66.30', '3.1': 'avc1.42001f'},
		     'main'     : {'3.0': 'avc1.77.30', '3.1': 'avc1.4d001f', '4.0': 'avc1.4d0028'},
		     'high'	: {'3.1': 'avc1.64001f','4.0': 'avc1.640028', '4.1': 'avc1.640028'} }

M3U8_AudioCodecs = { 'aac-lc' : 'mp4a.40.2' } 

DEFAULT_AUDIO_CODEC = 'aac-lc'

BANDWIDTH_FACTOR = 1.254
#BANDWIDTH_FACTOR = 1.225
#AVERAGE_BANDWITH_FACTOR = 1.084
AVERAGE_BANDWITH_FACTOR = 1.15

def M3U8GetFiles(playlist):
    
    FileList = []

    with open(playlist) as f:
	content = f.readlines()
	f.close()

    i = 0
    m3u8_end = False
    for info in content:
	if i == 0:
	    if not info.startswith('#EXTM3U'):
		raise M3U8Error('File: %s not a valid m3u8 file' % playlist)
	    i = i + 1
	else:
	    if info.startswith('#EXT-X-ENDLIST'):
		m3u8_end = True
	    else:
		if not info.startswith('#'):
		    FileList.append(info.replace('\n',''))

    if not m3u8_end:
	raise M3U8Error('File: %s is an incomplete playlist' % playlist)

    return FileList



class M3U8(object):
    def __init__(self, playlist, version=3):
	self.header	= '#EXTM3U'
	self.version   	= version
	self.playlist  	= playlist
	self.rendition 	= []

    def addRendition(self, profile, level, bitrate, resolution, filename):
	self.rendition.append({'profile': profile, 'level': level, 'bitrate':bitrate, 'resolution': resolution, 'filename':filename})


    def getBandwidth(self, bitrate):
	return int(bitrate) * 1000 * BANDWIDTH_FACTOR

    def getAverageBandwidth(self,bitrate):
	return int(bitrate) * 1000 * AVERAGE_BANDWITH_FACTOR

    def getCodec(self, profile, level):
	if profile in M3U8_VideoCodecs.keys():
	    if level in M3U8_VideoCodecs[profile].keys():
		return '"%s,%s"' % (M3U8_VideoCodecs[profile][level],
				    M3U8_AudioCodecs['aac-lc'])
	    else:
		raise M3U8Error('Unknow level: %s at profile: %s' % level, profile)
	else:
	    raise M3U8Error('Unknow profile: %s' % profile)

    def save(self, path):
    
	if not path.endswith('/'):
	    path = path + '/'

	try:
	    file = open(path + self.playlist, 'wt')
	except IOError as e:
	    raise M3U8Error(e)


	str_playlist = '%s\n%s%d\n' % (self.header, '#EXT-X-VERSION:', self.version)

	for r in self.rendition:
	    str_rendition = '#EXT-X-STREAM-INF:BANDWIDTH=%d,AVERAGE-BANDWIDTH=%d,CODECS=%s,RESOLUTION=%s\n%s\n' % (self.getBandwidth(r['bitrate']),
														   self.getAverageBandwidth(r['bitrate']),
														   self.getCodec(r['profile'],r['level']),
														   r['resolution'],r['filename'])
	    str_playlist = str_playlist + str_rendition

	file.write(str_playlist)
	file.close()





#x = M3U8('flenson.m3u8')
#x.addRendition('baseline', '3.0', 250+64, '480x270', 'flenson_270k.m3u8')
#x.addRendition('baseline', '3.0', 375+64, '480x270', 'flenson_375k.m3u8')
#M3U8GetFiles('/mnt/www/zolecha/cdnplayboy/ffmpeg/output/zolecha_375.m3u8')
#x.save('./')


    

    