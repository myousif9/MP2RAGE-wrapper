from bg_remover_wrapper import bgremover
from nipype.interfaces.io import DataGrabber, DataSink
from nipype.interfaces import utility as niu
from nipype.pipeline import Node, MapNode, Workflow
from nipype.interfaces.utility  import Function
from bids.layout import BIDSLayout
import sys
import os

def replace_slash_fn(filename):  
        renamed="_".join(str(filename).split("/"))            
        return renamed
replace_slash = Function(input_names=["filename"],
                             output_names=["renamed"],
                             function=replace_slash_fn)

def create_pipeline_bgremover(bids_dir,work_dir,out_dir,subjects,sessions,reg,uni_match_pattern,inv1_match_pattern,inv2_match_pattern):
        layout=BIDSLayout(bids_dir)
        for subject in subjects:
                if layout.get_sessions(subject=subject)==[]:
                        if sessions==['.*']:
                                first_uni_files=first_uni_files+layout.get(subject=subject,modality='anat',extensions='.*UNI.*.nii.*',)
                                first_inv1_files=first_inv1_files+layout.get(subject=subject,modality='anat',extention='.*inv-1.*.nii.*')
                                first_inv2_files=first_inv2_files+layout.get(subject=subject,modality='anat',extention='.*inv-2.*.nii.*')
                        else:
                                print("Warning: Session filter applied, but subject "+subject+"has no bids session information. This subject has been ignored.")
                else:
                        for session in sessions:
                                first_uni_files=first_uni_files+layout.get(subject=subject,session=session,modality='anat',extensions='.*UNI.*.nii.*',)
                                first_inv1_files=first_inv1_files+layout.get(subject=subject,session=session,modality='anat',extention='.*inv-1.*.nii.*')
                                first_inv2_files=first_inv2_files+layout.get(subject=subject,session=session,modality='anat',extention='.*inv-2.*.nii.*')
        uni_folders=[]
        for img in first_uni_files:
                full_dirname=os.path.dirname(img.filename)
                remove_base_dir=full_dirname.replace(bids_dir,'')
                remove_leading_slash=remove_base_dir.lstrip(os.sep)
                uni_folders.append(remove_leading_slash)
        list(set(uni_folders)).sort()

        inv1_folders=[]
        for img in first_inv1_files:
                full_dirname=os.path.dirname(img.filename)
                remove_base_dir=full_dirname.replace(bids_dir,'')
                remove_leading_slash=remove_base_dir.lstrip(os.sep)
                inv1_folders.append(remove_leading_slash)
        list(set(inv1_folders)).sort()

        inv2_folders=[]
        for img in first_inv2_files:
                full_dirname=os.path.dirname(img.filename)
                remove_base_dir=full_dirname.replace(bids_dir,'')
                remove_leading_slash=remove_base_dir.lstrip(os.sep)
                inv2_folders.append(remove_leading_slash)
        list(set(inv2_folders)).sort()

        infosource_uni = Node(niu.IdentityInterface(fields=['uni']), name='infosource_uni')
        infosource_uni.iterables = ('uni',uni_folders)
        infosource_inv1 = Node(niu.IdentityInterface(fields=['inv1']),name='infosource_inv1')
        infosource_inv1.iterables = ('inv1',inv1_folders)
        infosource_inv2 = Node(niu.IdentityInterface(fields=['inv2']),name='infosource_inv2')
        infosource_inv2.iterables = ('inv2',inv2_folders)

        datasource=Node(DataGrabber(infields=['uni','inv1','inv2'],outfields=['uni_image','inv1_image','inv2_image']),name='datasource')
        datasource.inputs.field_template=dict(
                uni_image='%s/'+uni_match_pattern+'.nii*',
                inv1_image='%d/'+inv1_match_pattern+'.nii*',
                inv2_image='%f/'+inv2_match_pattern+'.nii*')
        datasource.inputs.sort_filelist=True
        datasource.inputs.template="*"
        datasource.inputs.base_directory=bids_dir
        
        t1w_gen = Node(bgremover(reg=reg),name = 'background_remover')
        
        datasink = Node(DataSink(),name = 'datasink')
        datasink.inputs.base_directory = out_dir +'/bg_remover/'
        datasink.inputs.parameterization=False

        rename_infosource=Node(replace_slash,"rename_infosource")
        rename_t1w=Node(niu.Rename(format_string="%(uni)s-T1w", keep_ext = True),"rename_T1w")
        
        pipelineDir=work_dir
        wf = Workflow(name='bg_remover')
        wf.base_dir=pipelineDir
        wf.config['excecution']['remove_unnecessary_outputs']=False
        wf.connect([
                        (infosource_uni,datasource,[('uni','uni')]),
                        (infosource_inv1,datasource,[('inv1','inv1')]),
                        (infosource_inv2,datasource,[('inv2','inv2')]),
                        (datasource, t1w_gen,  [('uni_image','uni_in'),
                                                ('inv1_image','inv1_in'),
                                                ('inv2_image','inv2_in')]),
                        (t1w_gen, datasink,    [('out_file','in_file')]),
                        (infosource_uni,rename_infosource, [('uni','filename')]),
                        (rename_infosource,rename_t1w,[('renamed','uni')]),
                        (rename_t1w,datasink,[('out_file','@')])
                        ])
        return wf
