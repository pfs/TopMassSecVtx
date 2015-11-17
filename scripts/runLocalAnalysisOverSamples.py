#!/usr/bin/env python
import os,sys
import json
import optparse
import commands
import LaunchOnCondor

"""
Gets the value of a given item
(if not available a default value is returned)
"""
def getByLabel(desc,key,defaultVal=None) :
    try :
        return desc[key]
    except KeyError:
        return defaultVal


#configure
usage = 'usage: %prog [options]'
parser = optparse.OptionParser(usage)
parser.add_option('-e', '--exe'        ,    dest='theExecutable'      , help='excecutable'                           , default='')
parser.add_option('-s', '--sub'        ,    dest='queue'              , help='batch queue'                           , default='')
parser.add_option('-R', '--R'          ,    dest='requirementtoBatch' , help='requirement for batch queue'           , default='pool>30000')
parser.add_option('-j', '--json'       ,    dest='samplesDB'          , help='samples json file'                     , default='')
parser.add_option('-d', '--dir'        ,    dest='indir'              , help='input directory or tag in json file'   , default='aoddir')
parser.add_option('-o', '--out'        ,    dest='outdir'             , help='output directory'                      , default='')
parser.add_option('-t', '--tag'        ,    dest='onlytag'            , help='process only samples matching this tag', default='')
parser.add_option('--onlySplits'       ,    dest='onlysplits'         , help='process only this split file (to be used together with --tag)', default='')
parser.add_option('-n', '--n'          ,    dest='fperjob'            , help='input files per job'                   , default=-1,  type=int)
parser.add_option('-p', '--pars'       ,    dest='params'             , help='extra parameters for the job'          , default='')
parser.add_option('-c', '--cfg'        ,    dest='cfg_file'           , help='base configuration file template'      , default='')
parser.add_option('-r', "--report"     ,    dest='report'             , help='If the report should be sent via email', default=False, action="store_true")
parser.add_option('-f', "--forceHash"  ,    dest='forceHash'          , help='Force to use this hash',                 default=commands.getstatusoutput('git rev-parse --short HEAD')[1])
(opt, args) = parser.parse_args()
scriptFile=os.path.expandvars('${CMSSW_BASE}/bin/${SCRAM_ARCH}/wrapLocalAnalysisRun.sh')

def stringRangeToList(stringrange):
    """
    Converts strings like 1,4,5 or 1-4 or 1-9,11,14
    to lists. I.e. the above examples would be:
    [1,4,5], [1,2,3,4], and [1,2,3,4,5,6,7,8,9,11,14]
    """
    result = []
    for part in stringrange.split(','):
        if '-' in part:
            a, b = part.split('-')
            a, b = int(a), int(b)
            result.extend(range(a, b+1))
        else:
            a = int(part)
            result.append(a)
    return result

splits_to_process = []
if len(opt.onlysplits)>0:
    splits_to_process = stringRangeToList(opt.onlysplits)
    print "Only processing these splits:", splits_to_process

split=1
segment=0

#open the file which describes the sample
jsonFile = open(opt.samplesDB,'r')
try:
    procList=json.load(jsonFile,encoding='utf-8').items()
except ValueError as e:
    print 40*'#'
    print "Error parsing JSON file, check syntax!"
    print e
    print 40*'#'
    exit(-1)

#append the latest tag to the dir
opt.outdir += '/'+opt.forceHash

FarmDirectory                      = opt.outdir+"/FARM"
JobName                            = opt.theExecutable
LaunchOnCondor.Jobs_RunHere        = 1
LaunchOnCondor.Jobs_Queue          = opt.queue
LaunchOnCondor.Jobs_LSFRequirement = '"'+opt.requirementtoBatch+'"'
LaunchOnCondor.Jobs_EmailReport    = opt.report
LaunchOnCondor.SendCluster_Create(FarmDirectory, JobName)



#run over sample
for proc in procList :

    #run over processes
    for desc in proc[1] :

        #run over items in process
        isdata=getByLabel(desc,'isdata',False)
        mctruthmode=getByLabel(desc,'mctruthmode',0)

        data = desc['data']
        for d in data :
            origdtag = getByLabel(d,'dtag','')
            dtag = origdtag
            xsec = getByLabel(d,'xsec',-1)
            br = getByLabel(d,'br',[])
            suffix = str(getByLabel(d,'suffix' ,""))
            if len(opt.onlytag)>0:
                if not opt.onlytag in dtag: continue

            if mctruthmode!=0 : dtag+='_filt'+str(mctruthmode)

            if(xsec>0 and not isdata) :
                for ibr in br :  xsec = xsec*ibr
            split=getByLabel(d,'split',1)

            for segment in range(0,split):
                if(split==1):
                    eventsFile=opt.indir + '/' + origdtag + '.root'
                else:
                    eventsFile=opt.indir + '/' + origdtag + '_' + str(segment) + '.root'

                if len(opt.onlytag)>0 and len(splits_to_process)>0:
                    if not segment in splits_to_process: continue

                if(eventsFile.find('/store/')==0)  : eventsFile = 'root://eoscms//eos/cms/'+eventsFile

                #create the cfg file
                sedcmd = 'sed \"s%@input%' + eventsFile +'%;s%@outdir%' + opt.outdir +'%;s%@isMC%' + str(not isdata) + '%;s%@mctruthmode%'+str(mctruthmode)+'%;s%@xsec%'+str(xsec)+'%;'
                sedcmd += 's%@cprime%'+str(getByLabel(d,'cprime',-1))+'%;'
                sedcmd += 's%@brnew%' +str(getByLabel(d,'brnew' ,-1))+'%;'
                sedcmd += 's%@suffix%' +suffix+'%;'
                if(opt.params.find('@useMVA')<0) :          opt.params = '@useMVA=False ' + opt.params
                if(opt.params.find('@weightsFile')<0) :     opt.params = '@weightsFile= ' + opt.params
                if(opt.params.find('@evStart')<0) :         opt.params = '@evStart=0 '    + opt.params
                if(opt.params.find('@evEnd')<0) :           opt.params = '@evEnd=-1 '     + opt.params
                if(opt.params.find('@saveSummaryTree')<0) : opt.params = '@saveSummaryTree=False ' + opt.params
                if(opt.params.find('@runSystematics')<0) :  opt.params = '@runSystematics=False '  + opt.params
                if(opt.params.find('@jacknife')<0) :        opt.params = '@jacknife=-1 ' + opt.params
                if(opt.params.find('@jacks')<0) :           opt.params = '@jacks=-1 '    + opt.params
                if(len(opt.params)>0) :
                    extracfgs = opt.params.split(' ')
                    for icfg in extracfgs :
                        varopt=icfg.split('=')
                        if(len(varopt)<2) : continue
                        sedcmd += 's%' + varopt[0] + '%' + varopt[1] + '%;'
                sedcmd += '\"'
                if(split==1):
                    cfgfile=opt.outdir +'/'+ dtag + suffix + '_cfg.py'
                else:
                    cfgfile=opt.outdir +'/'+ dtag + suffix + '_' + str(segment) + '_cfg.py'
                
                os.system('cat ' + opt.cfg_file + ' | ' + sedcmd + ' > ' + cfgfile)

                #run the job
                if len(opt.queue)==0 :
                    os.system(opt.theExecutable + ' ' + cfgfile)
                else :
                    #old version
                    #localParams='-exe=%s -cfg=%s'%(opt.theExecutable,cfgfile)
                    #batchCommand='submit2batch.sh -q%s -R\"%s\" -J%s%d %s %s'%(opt.queue,opt.requirementtoBatch,d['dtag'],segment,scriptFile,localParams)
                    #os.system(batchCommand)
                    LaunchOnCondor.SendCluster_Push(["BASH", str(opt.theExecutable + ' ' + cfgfile)])

LaunchOnCondor.SendCluster_Submit()
