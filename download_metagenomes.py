import sarge
import os
import glob
import xml.etree.ElementTree as ET
import sys
import logging
import click

logger = logging.getLogger(__name__)

database = 'https://genome.jgi.doe.gov'

def curlcmd(url, database, destout):
    cmd = "curl '{database}{url}' -b cookies > {destout}".format(database = database,
            url = url, destout = destout)
    print(cmd)
    return cmd


@click.command(context_settings=dict(help_option_names=['-h','--help']))
@click.option('--username', help='img username')
@click.option('--password', help = 'img password')
@click.option('--log', default = None, help='designate log file')
@click.option('--xml-string', default = '*2019.xml', help='wildcard string for target xml files to read')
def download_jgi_metagenomes(username, password, log, xml_string):
    
    if log is None:
        log = logging.StreamHandler(sys.stdout)
        log.setLevel(logging.INFO)
        logger.addHandler(log)
    else:
        logging.basicConfig(filename=log, level=logging.INFO)
    print('starting connection')
    sarge.run("curl 'https://signon.jgi.doe.gov/signon/create' --data-urlencode 'login={username}' --data-urlencode 'password={password}' -c cookies > /dev/null".format(username=username, password = password))

    xmls = glob.glob(xml_string)
    logger.info('Found the following xmls {}'.format(",".join(xmls)))
    
    for xml in xmls:
        logger.info('working with {}'.format(xml))
        # get name of 
        mgid = os.path.basename(xml).split(".")[0]

        # read xml tree of sample directory system
        tree = ET.parse(xml)
        root = tree.getroot()

        # make output directory
        
        outdir = mgid
        if not os.path.exists(outdir):
            os.mkdir(outdir)
            logger.info('created {}'.format(outdir))
        else:
            logger.info('{} already exists'.format(outdir))

        # MG Bins
        # create directory for mg bins
        bindir = os.path.join(outdir, 'bins')
        
        logger.info('writing mg bins here: {}'.format(bindir))
        if not os.path.exists(bindir):
            os.mkdir(bindir)

        # download bins
        
        for child in root:
            if child.attrib['name'] == 'Binning Data':

                for binchild in child:
                    filename = binchild.attrib['filename']
                    url = binchild.attrib['url']
                    destout = os.path.join(bindir, filename)

                    if not os.path.exists(destout):
                        cmd = curlcmd(url, database, destout)
                        logger.info(cmd)
                        sarge.run(cmd)

        # Filtered Raw Data
        # create directory
        print('working on filtered raw data')
        frddir = os.path.join(outdir, 'filtered_raw_data')
        if not os.path.exists(frddir):
            os.mkdir(frddir)

        # download certain files
        keep_file_phrases = ['filtered-report', 'METAGENOME.fastq.gz']
        for child in root:
            if child.attrib['name'] == 'Filtered Raw Data':

                for frchild in child:
                    for phrase in keep_file_phrases:
                        if phrase in frchild.attrib['filename']:
                            filename = frchild.attrib['filename']

                            destout = os.path.join(frddir, filename)
                            url = frchild.attrib['url']

                            if not os.path.exists(destout):
                                cmd = curlcmd(url, database, destout)
                                logger.info(cmd)
                                sarge.run(cmd)
        # MG tables
        mgtbldir = os.path.join(outdir, 'mg_report_tables')

        if not os.path.exists(mgtbldir):
            os.mkdir(mgtbldir)


        for child in root:
            if child.attrib['name'] == 'Metagenome Report Tables':
                for stepchild in child:
                    filename = stepchild.attrib['filename']
                    url = stepchild.attrib['url']

                    destout = os.path.join(mgtbldir, filename)
                    if not os.path.exists(destout):
                        cmd = curlcmd(url, database, destout)
                        logger.info(cmd)
                        sarge.run(cmd)
        # IMG data
        imgdir = os.path.join(outdir, 'img_data')

        if not os.path.exists(imgdir):
            os.mkdir(imgdir)

        for child in root:
            if child.attrib['name'] == 'IMG Data':
                for stepchild in child:
                    filename = stepchild.attrib['filename']
                    if filename.endswith('.tar.gz'):
                        url = stepchild.attrib['url']

                        destout = os.path.join(imgdir, filename)
                        if not os.path.exists(destout):
                            cmd = curlcmd(url, database, destout)
                            logger.info(cmd)
                            sarge.run(cmd)
                            
if __name__=='__main__':
    download_jgi_metagenomes()