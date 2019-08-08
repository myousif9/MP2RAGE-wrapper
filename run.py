from create_pipeline_bg_remover import create_pipeline_bgremover
import os

if __name__=="__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter
    from nipype import config, logging
    defstr = ' (default %(default)s)'
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument('bids_dir',help='the directory with the input dataset formatted according to the BIDS standard.')
    parser.add_argument('output_dir', help='The directory where the output files '
                        'should be stored. If you are running group level analysis '
                        'this folder should be prepopulated with the results of the'
                        'participant level analysis.')
    parser.add_argument('--participant_label', help='The label(s) of the participant(s) that should be analyzed. The label '
                        'corresponds to sub-<participant_label> from the BIDS spec '
                        '(so it does not include "sub-"). If this parameter is not '
                        'provided all subjects should be analyzed. Multiple '
                        'participants can be specified with a space separated list.',
                        default=['.*'],
                        nargs="+")    
    parser.add_argument('--session_label', help='The label(s) of the session(s) that should be analyzed. The label '
                        'corresponds to ses-<session_label> from the BIDS spec '
                        '(so it does not include "ses-"). If this parameter is not '
                        'provided all sessions should be analyzed. Multiple '
                        'sessions can be specified with a space separated list.',
                        default=['.*'],
                        nargs="+")    
    parser.add_argument("-w", "--work_dir", dest="work_dir",
                        help="Work directory. Defaults to <output_dir>/scratch")
    parser.add_argument("-l", "--log_dir", dest="log_dir",
                        help="Nipype output log directory. Defaults to <output_dir>/log")
    parser.add_argument("-c", "--crash_dir", dest="crash_dir",
                        help="Nipype crash dump directory. Defaults to <output_dir>/crash_dump")
    parser.add_argument("-p", "--plugin", dest="plugin",
                        default='Linear',
                        help="Plugin to use")
    parser.add_argument("--plugin_args", dest="plugin_args",
                        help="Plugin arguments")
    parser.add_argument("--keep_unnecessary_outputs", dest="keep_unnecessary_outputs",
                        action='store_true',default=False,
                        help="keep all nipype node outputs, even if unused")
    parser.add_argument('--uni_match_pattern', dest="uni_match_pattern",
                        default='*UNI*',
                        help='Pattern used to match UNI images and json files '
                        'in anat folder (leave extension out of pattern). The '
                        'pattern may contain simple shell-style wildcards a la '
                        'fnmatch. However, unlike fnmatch, filenames starting with '
                        'a dot are special cases that are not matched by \'*\' and '
                        '\'?\' patterns. Example usage: *acq-uni*')  
    parser.add_argument('--inv1_match_pattern', dest="inv1_match_pattern",
                        default='*inv-1*',
                        help='Pattern used to match inv1 images and json files '
                        'in anat folder (leave extension out of pattern). The '
                        'pattern may contain simple shell-style wildcards a la '
                        'fnmatch. However, unlike fnmatch, filenames starting with '
                        'a dot are special cases that are not matched by \'*\' and '
                        '\'?\' patterns. Example usage: *inv-1*')  
    parser.add_argument('--inv2_pattern', dest="inv2_match_pattern",
                        default='*inv-2*',
                        help='Pattern used to match inv2 images and json files '
                        'in anat folder (leave extension out of pattern). The '
                        'pattern may contain simple shell-style wildcards a la '
                        'fnmatch. However, unlike fnmatch, filenames starting with '
                        'a dot are special cases that are not matched by \'*\' and '
                        '\'?\' patterns. Example usage: *inv-2*')  
    parser.add_argument("--regularization", dest="regularization",
                        default=10,
                        help="regularization parameter")
    args = parser.parse_args()
    

    bids_dir=args.bids_dir
    out_dir=args.output_dir
    
    uni_match_pattern=args.uni_match_pattern
    inv1_match_pattern=args.inv1_match_pattern
    inv2_match_pattern=args.inv2_match_pattern  
    subjects=args.participant_label
    sessions=args.session_label
        
    if args.work_dir:
        work_dir = os.path.abspath(args.work_dir)
    else:
        work_dir = os.path.join(out_dir, 'scratch')
    if args.log_dir:
        log_dir = os.path.abspath(args.log_dir)
    else:
        tmp="log-"+"_".join(subjects)+'-'+"_".join(sessions)
        tmp=tmp.replace(".*","all").replace("*","star")
        log_dir = os.path.join(out_dir, 'logs',tmp)
    if args.crash_dir:
        crash_dir = os.path.abspath(args.crash_dir)
    else:
        crash_dir = os.path.join(out_dir, 'crash_dump')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    config.update_config({'logging': {
                                        'log_directory': log_dir,
                                        'log_to_file': True,
                                      },
                           'execution': {
                                          'crashdump_dir': crash_dir,
                                          'crashfile_format': 'txt',                                      
                                      }})
    logging.update_logging(config)
    
    plugin=args.plugin
    plugin_args=args.plugin_args
    keep_unnecessary_outputs=args.keep_unnecessary_outputs

    regularization = float(args.regularization)

    wf_bg_remover = create_pipeline_bgremover(bids_dir=bids_dir,
                                work_dir=work_dir,
                                out_dir=out_dir,
                                subjects=subjects,
                                sessions=sessions,
                                reg=regularization,
                                uni_match_pattern=uni_match_pattern,
                                inv1_match_pattern=inv1_match_pattern,
                                inv2_match_pattern=inv2_match_pattern)
    if args.plugin_args:
        exec_bg_remover=wf_bg_remover.run(args.plugin, plugin_args=eval(args.plugin_args))
    else:
        exec_bg_remover=wf_bg_remover.run(args.plugin)