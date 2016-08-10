import subprocess
import shlex
import sys
import logging
import os
import datetime
import math
import glob
import pipes
from dateutil import relativedelta
##################################
# Generate tooltip thumbnail images & corresponding WebVTT file for a video (e.g MP4).
# Final product is one *_sprite.jpg file and one *_thumbs.vtt file.
#
# DEPENDENCIES: required: ffmpeg & imagemagick
#               optional: sips (comes with MacOSX) - yields slightly smaller sprites
#    download ImageMagick: http://www.imagemagick.org/script/index.php OR http://www.imagemagick.org/script/binary-releases.php (on MacOSX: "sudo port install ImageMagick")
#    download ffmpeg: http://www.ffmpeg.org/download.html
# jwplayer reference: http://www.longtailvideo.com/support/jw-player/31778/adding-tooltip-thumbnails/
#
# TESTING NOTES: Tested putting time gaps between thumbnail segments, but had no visual effect in JWplayer, so omitted.
#                Tested using an offset so that thumbnail would show what would display mid-way through clip rather than for the 1st second of the clip, but was not an improvement.
##################################

#TODO determine optimal number of images/segment distance based on length of video? (so longer videos don't have huge sprites)

#USE_SIPS = False #True to use sips if using MacOSX (creates slightly smaller sprites), else set to False to use ImageMagick
#THUMB_RATE_SECONDS=5 # every Nth second take a snapshot
#THUMB_WIDTH=150 #100-150 is width recommended by JWPlayer; I like smaller files
SKIP_FIRST=True #True to skip a thumbnail of second 1; often not a useful image, plus JWPlayer doesn't seem to show it anyway, and user knows beginning without needing preview
#ASPECT_RATIO="150x84"
#SPRITE_NAME = "sprite.jpg" #jpg is much smaller than png, so using jpg
#VTTFILE_NAME = "thumbs.vtt"
#THUMB_OUTDIR = "thumbs"
#USE_UNIQUE_OUTDIR = False #true to make a unique timestamped output dir each time, else False to overwrite/replace existing outdir
TIMESYNC_ADJUST = -.5 #set to 1 to not adjust time (gets multiplied by thumbRate); On my machine,ffmpeg snapshots show earlier images than expected timestamp by about 1/2 the thumbRate (for one vid, 10s thumbrate->images were 6s earlier than expected;45->22s early,90->44 sec early)
logger = logging.getLogger("thumbsmaker")
logSetup=False
#LOG_PATH = "/home/npajoni/Downloads/thums_log"

class ImageTask():
    """small wrapper class as convenience accessor for external scripts"""
    def __init__(self, input_path = '', input_file = '', basename = '', outdir = '', rate = '',
                 width = '', height = '', aspect_ratio = '', sp_flag = False, sp_quality = ''):
        #if not os.path.exists(videofile):
        #    sys.exit("File does not exist: %s" % videofile)
        #basefile = os.path.basename(videofile)
        #basename = os.path.splitext(basefile)[0]
        #basefile_nospeed = removespeed(basefile) #strip trailing speed suffix from file/dir names, if present
        #newoutdir = makeOutDir(basename)
        #fileprefix,ext = os.path.splitext(basefile_nospeed)
        #spritefile = os.path.join(newoutdir,"%s_%s" % (fileprefix,SPRITE_NAME))
        #spritefile = os.path.join(outdir,"%s.jpg" % (basename))
        #vttfile = os.path.join(newoutdir,"%s_%s" % (fileprefix,VTTFILE_NAME))
        #vttfile = os.path.join(outdir, "%s.vtt" % (basename))


        #self.videofile  = videofile
        #self.vttfile       = vttfile
        #self.spritefile    = spritefile
        self.input_path     = input_path
        self.input_filename = input_file
        self.basename       = basename
        self.outdir         = outdir
        self.rate           = rate
        self.width          = width
        self.height         = height
        self.aspect_ratio   = aspect_ratio
        self.sp_flag        = sp_flag
        self.sp_quality     = sp_quality


def makeOutDir(outdir):
#    """create unique output dir based on video file name and current timestamp"""
    #base,ext = os.path.splitext(videofile)
    #script = sys.argv[0]
    #basepath = os.path.dirname(os.path.abspath(script)) #make output dir always relative to this script regardless of shell directory
    #if len(THUMB_OUTDIR)>0 and THUMB_OUTDIR[0]=='/':
    #    outputdir = THUMB_OUTDIR
    #else:
    #    outputdir = os.path.join(basepath,THUMB_OUTDIR)
    #if USE_UNIQUE_OUTDIR:
    #    newoutdir = "%s.%s" % (os.path.join(outputdir,base),datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    #else:
    #    newoutdir = "%s_%s" % (os.path.join(outputdir,base),"vtt")
    #newoutdir = outputdir
    if not os.path.exists(outdir):
        logger.info("Making dir: %s" % outdir)
        os.makedirs(outdir)
    elif os.path.exists(outdir):
        #remove previous contents if reusing outdir
        files = os.listdir(outdir)
        print "Removing previous contents of output directory: %s" % outdir
        for f in files:
            os.unlink(os.path.join(outdir,f))
#    return outdir

def doCmd(cmd,logger=logger):  #execute a shell command and return/print its output
    logger.info( "START [%s] : %s " % (datetime.datetime.now(), cmd))
    args = shlex.split(cmd) #tokenize args
    output = None
    try:
        output = subprocess.check_output(args, stderr=subprocess.STDOUT) #pipe stderr into stdout
    except Exception, e:
        ret = "ERROR   [%s] An exception occurred\n%s\n%s" % (datetime.datetime.now(),output,str(e))
        logger.error(ret)
        raise e #todo ?
    ret = "END   [%s]\n%s" % (datetime.datetime.now(),output)
    logger.info(ret)
    sys.stdout.flush()
    return output

def takesnaps(ffmpeg, videofile, basename, newoutdir,thumbRate, resolution, aspect_ratio):
    """
    take snapshot image of video every Nth second and output to sequence file names and custom directory
        reference: https://trac.ffmpeg.org/wiki/Create%20a%20thumbnail%20image%20every%20X%20seconds%20of%20the%20video
    """
    rate = "1/%d" % thumbRate # 1/60=1 per minute, 1/120=1 every 2 minutes
    cmd = "%s -loglevel error -i %s -f image2 -bt 20M -vf fps=%s -s %s -aspect %s %s/%s_%%03d.jpg" % (ffmpeg, pipes.quote(videofile), rate, resolution, aspect_ratio, pipes.quote(newoutdir), basename)
    doCmd (cmd)
    if SKIP_FIRST:
        #remove the first image
        logger.info("Removing first image, unneeded")
        os.unlink("%s/%s_001.jpg" % (newoutdir, basename))
    count = len(os.listdir(newoutdir))
    logger.info("%d thumbs written in %s" % (count,newoutdir))
    #return the list of generated files
    return count,get_thumb_images(newoutdir, basename)

def get_thumb_images(newdir, basename):
    return glob.glob("%s/%s_*.jpg" % (newdir, basename))

#def resize(files):
#    """change image output size to 100 width (originally matches size of video)
#      - pass a list of files as string rather than use '*' with sips command because
#        subprocess does not treat * as wildcard like shell does"""
#    if USE_SIPS:
#        # HERE IS MAC SPECIFIC PROGRAM THAT YIELDS SLIGHTLY SMALLER JPGs
#        doCmd("sips --resampleWidth %d %s" % (THUMB_WIDTH," ".join(map(pipes.quote, files))))
#    else:
#        # THIS COMMAND WORKS FINE TOO AND COMES WITH IMAGEMAGICK, IF NOT USING A MAC
#        doCmd("mogrify -geometry %dx %s" % (THUMB_WIDTH," ".join(map(pipes.quote, files))))

def get_geometry(file):
    """execute command to give geometry HxW+X+Y of each file matching command
       identify -format "%g - %f\n" *         #all files
       identify -format "%g - %f\n" onefile.jpg  #one file
     SAMPLE OUTPUT
        100x66+0+0 - _tv001.jpg
        100x2772+0+0 - sprite2.jpg
        4200x66+0+0 - sprite2h.jpg"""
    geom = doCmd("""identify -format "%%g - %%f\n" %s""" % pipes.quote(file))
    parts = geom.split("-",1)
    return parts[0].strip() #return just the geometry prefix of the line, sans extra whitespace

def makevtt(spritefile,numsegments,coords,gridsize,writefile,thumbRate):
    """generate & write vtt file mapping video time to each image's coordinates
    in our spritemap"""
    #split geometry string into individual parts
    ##4200x66+0+0     ===  WxH+X+Y
    #if not thumbRate:
    #    thumbRate = THUMB_RATE_SECONDS
    wh,xy = coords.split("+",1)
    w,h = wh.split("x")
    w = int(w)
    h = int(h)
    #x,y = xy.split("+")
#======= SAMPLE WEBVTT FILE=====
#WEBVTT
#
#00:00.000 --> 00:05.000
#/assets/thumbnails.jpg#xywh=0,0,160,90
#
#00:05.000 --> 00:10.000
#/assets/preview2.jpg#xywh=160,0,320,90
#
#00:10.000 --> 00:15.000
#/assets/preview3.jpg#xywh=0,90,160,180
#
#00:15.000 --> 00:20.000
#/assets/preview4.jpg#xywh=160,90,320,180
#==== END SAMPLE ========
    basefile = os.path.basename(spritefile)
    vtt = ["WEBVTT",""] #line buffer for file contents
    if SKIP_FIRST:
        clipstart = thumbRate  #offset time to skip the first image
    else:
        clipstart = 0
    # NOTE - putting a time gap between thumbnail end & next start has no visual effect in JWPlayer, so not doing it.
    clipend = clipstart + thumbRate
    adjust = thumbRate * TIMESYNC_ADJUST
    for imgnum in range(1,numsegments+1):
        xywh = get_grid_coordinates(imgnum,gridsize,w,h)
        start = get_time_str(clipstart,adjust=adjust)
        end  = get_time_str(clipend,adjust=adjust)
        clipstart = clipend
        clipend += thumbRate
        vtt.append("Img %d" % imgnum)
        vtt.append("%s --> %s" % (start,end)) #00:00.000 --> 00:05.000
        vtt.append("%s#xywh=%s" % (basefile,xywh))
        vtt.append("") #Linebreak
    vtt =  "\n".join(vtt)
    #output to file
    writevtt(writefile,vtt)

def get_time_str(numseconds,adjust=None):
    """ convert time in seconds to VTT format time (HH:)MM:SS.ddd"""
    if adjust: #offset the time by the adjust amount, if applicable
        seconds = max(numseconds + adjust, 0) #don't go below 0! can't have a negative timestamp
    else:
        seconds = numseconds
    delta = relativedelta.relativedelta(seconds=seconds)
    return "%02d:%02d:%02d.000" % (delta.hours,delta.minutes, delta.seconds)

def get_grid_coordinates(imgnum,gridsize,w,h):
    """ given an image number in our sprite, map the coordinates to it in X,Y,W,H format"""
    y = (imgnum - 1)/gridsize
    x = (imgnum -1) - (y * gridsize)
    imgx = x * w
    imgy =y * h
    return "%s,%s,%s,%s" % (imgx,imgy,w,h)

def makesprite(outdir, basename, spritefile, coords, gridsize, sp_quality):
    """montage _tv*.jpg -tile 8x8 -geometry 100x66+0+0 montage.jpg  #GRID of images
           NOT USING: convert tv*.jpg -append sprite.jpg     #SINGLE VERTICAL LINE of images
           NOT USING: convert tv*.jpg +append sprite.jpg     #SINGLE HORIZONTAL LINE of images
     base the sprite size on the number of thumbs we need to make into a grid."""
    grid = "%dx%d" % (gridsize,gridsize)
    cmd = "montage %s/%s_*.jpg -quality %s -tile %s -geometry %s %s" % (pipes.quote(outdir), basename, sp_quality, grid, coords, pipes.quote(spritefile))#if video had more than 144 thumbs, would need to be bigger grid, making it big to cover all our case
    doCmd(cmd)

def writevtt(vttfile,contents):
    """ output VTT file """
    with open(vttfile,mode="w") as h:
        h.write(contents)
    logger.info("Wrote: %s" % vttfile)

#def removespeed(videofile):
#    """some of my files are suffixed with datarate, e.g. myfile_3200.mp4;
#     this trims the speed from the name since it's irrelevant to my sprite names (which apply regardless of speed);
#     you won't need this if it's not relevant to your filenames"""
#    videofile = videofile.strip()
#    speed = videofile.rfind("_")
#    speedlast = videofile.rfind(".")
#    maybespeed = videofile[speed+1:speedlast]
#    try:
#        int(maybespeed)
#        videofile = videofile[:speed] + videofile[speedlast:]
#    except:
#        pass
#    return videofile

def runImageTask(task, ffmpeg, log_path):
    addLogging(log_path)
    thumbRate   = task.rate
    outdir      = task.outdir
    basename    = task.basename
    sp_quality  = task.sp_quality
    sp_flag     = task.sp_flag
    asp_rat     = task.aspect_ratio

    try:
        makeOutDir(outdir)
    except:
        ret = "ERROR   [%s] Could not create output path: %s" % (datetime.datetime.now(), output)
        logger.error(ret)

    if task.input_path.endswith("/"):
        videofile = task.input_path + task.input_filename
    else:
        videofile = task.input_path + "/" + task.input_filename

    if not os.path.exists(ffmpeg):
        sys.exit("ffmpeg bin does not exist: %s" % ffmpeg)

    resolution, asp_rat = getResolution(task.width, task.height, asp_rat)

    #create snapshots
    numfiles,thumbfiles = takesnaps(ffmpeg, videofile, basename, outdir, thumbRate, resolution, asp_rat)
    #resize them to be mini
    #resize(thumbfiles)

    if sp_flag == True:
        #get coordinates from a resized file to use in spritemapping
        spritefile = os.path.join(outdir, "%s.jpg" % (basename))
        vttfile = os.path.join(outdir, "%s.vtt" % (basename))

        gridsize = int(math.ceil(math.sqrt(numfiles)))
        coords = get_geometry(thumbfiles[0]) #use the first file (since they are all same size) to get geometry settings

        #convert small files into a single sprite grid
        makesprite(outdir, basename, spritefile, coords, gridsize, sp_quality)

        #generate a vtt with coordinates to each image in sprite
        makevtt(spritefile,numfiles,coords,gridsize,vttfile, thumbRate)

        files = os.listdir(outdir)
        print "Removing temporal contents of output directory: %s" % outdir
        for f in files:
            pattern = "%s_" % basename
            if f.startswith(pattern):
                os.unlink(os.path.join(outdir,f))

def addLogging(log_path):
    global logSetup
    if not logSetup:
        #basescript = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        LOG_FILENAME = '%s'% (log_path) #new log per job so we can run this program concurrently
        #CONSOLE AND FILE LOGGING
        print "Writing log to: %s" % LOG_FILENAME
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(LOG_FILENAME)
        logger.addHandler(handler)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)
        logSetup = True #set flag so we don't reset log in same batch


#if __name__ == "__main__":
#    if not len(sys.argv) > 1 :
#        sys.exit("Please pass the full path or url to the video file for which to create thumbnails.")
#    if len(sys.argv) == 3:
#        THUMB_OUTDIR = sys.argv[2]
#    videofile = sys.argv[1]
#    task = SpriteTask(videofile)
#    run(task)

def calcAspectRatio(w,h):
    fw   = float(w)
    fh   = float(h)
    err  = 0.05 # Error
    rel  = round(fw/fh,2)
    acum = 0.0
    i    = 1
    while True:
        acum = acum + rel
        mant = acum - int(acum)
        if mant < err:
            return '%d:%d' % (int(acum),i)
        i = i + 1

def getAspectRatio (ar):
    w,h = ar.split(':')
    return int(w), int(h)

def getResolution ( w = '', h = '', ar = ''):
    if w != '' and h != '':
        return ('%sx%s' % (w,h), calcAspectRatio(w,h))
    else:
        if w != '' and ar != '':
            iaw, iah = getAspectRatio(ar)
            iw = int(w)
            ih = iah * iw / iaw
            return ('%dx%d' % (iw,ih), ar)
        if h != '' and ar != '':
            iaw, iah = getAspectRatio(ar)
            ih = int(h)
            iw = ih * iaw / iah
            return ('%dx%d' % (iw,ih), ar)




"""
task = ImageTask()
task.input_path = "/mnt/test/procesados/"
task.input_filename = "001628.mxf"
task.outdir = "/home/npajoni/Downloads/test_image/"
task.rate = 5
task.resolution = "150x84"
task.width = "150"
task.aspect_ratio = "14:9"
task.basename = "Probando2"
task.sp_flag = True
task.sp_quality = "75"
ffmpeg = "/usr/bin/ffmpeg"
log_path = "/home/npajoni/Downloads/thums_log"
runImageTask(task, ffmpeg, log_path)
"""