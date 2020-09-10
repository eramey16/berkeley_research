  
;********************               
;;;;;;;;;;;;;;;;;;;;;      
;;; BENCH SETUP START
;;;;;;;;;;;;;;;;;;;;;
;********************
        'setup_bench':begin
           
                                ; first check that the loops are open
           dtlp=SHOW('ao.dtlp',error=error,status=status,/notrace)
           IF dtlp NE 0 THEN BEGIN
              txt='Please open the loops before running setup bench'
              tmp=DIALOG_MESSAGE(txt)
              TQ,data,txt
              RETURN   
           ENDIF
           
           IF data.rmag EQ 0 AND (data.archmode EQ 0 OR data.aoopsmode NE 0) THEN BEGIN
              txt = 'Please enter a valid R magnitude (not mR=0) and try again!'
              XMESSAGE, txt, 'OK', foo
              ABORT_ACQ,data
              RETURN
           ENDIF
           
           data.status[0:2] = [2,1,1]
           AOACQ_STATUS, data
           status = MODIFY('ao.frautabort', 0, err=err, /notrace) ; clear abort flag
           
           IF data.aoopsmode EQ 2 THEN BEGIN
; set the auto offset to off
              WIDGET_CONTROL,data.but_id[6],set_val='Offset to targ',set_uval='offset_target'

; set LGS to fixed           
              data.lgsmode=0    ; (M3 fixed) ;; CRN checked, aofmmove doesn't need changing for FST 20Apr2012
              tmp = MODIFY('ao.aofmmove', 0, stat=stat, err=err, /notrace)        
              tmp = MODIFY('ao.aolpmove', 0, stat=stat, err=err, /notrace)
              WIDGET_CONTROL, data.drp_id[2], set_droplist_select=data.lgsmode
              TQ,data,'Setting M3 to LGS FIXED'
           ENDIF
           
;;; Fill in structure containing parameters needed for bench setup

           setup = {obsdname: '', $
                    obamname: '', $
                    obasname: '', $
                    obwnname: '', $                    
                    obwfdsrc: 0L, $
                    obwpdsrc: 0L, $
                    fsmset: 1, $
                    tssset: 0, $
                    aofclgct: 0, $ 
                    aofcosoc: 1, $
                    aofctroc: 0, $
                    aotsgold: 0., $
                    guidwave: 0., $
                    wscnorfn: '', $
                    dtgain:   0.2, $
                    utgain:   0.1, $
                    dmgain:   0.3, $
                    dtsensor: 0, $
                    lsltlson: 0, $
                    aofotthr: 0., $
                    lst3pcrg: 0., $
                    stsetup:  0, $
                    obsi:     0., $
                    lbsetup:  0, $
                    aottmode: 0, $
                    aofomode: 0, $
                    lst3pcre: 0}   ;; CRN key on this k2 variable for K1 FST even though it is changed to lspntrce 

           case data.aoopsmode of ;; purely ngs mode
              0:begin
                 setup.obsdname = 'beamSplitter'
                 setup.obamname = 'mirror'
                 setup.obasname = 'ngs'
                 setup.obwnname = 'open'
                 setup.obwfdsrc = 0 ; manual
                 setup.obwpdsrc = 0 ; manual
                 setup.tssset = 0
                 setup.aofclgct = 0               
                 setup.aofcosoc = 1 ; one shot mode
                 setup.aofctroc = 0
                 setup.aotsgold = 1.
                 setup.guidwave = 0.63e-6
                 setup.dtgain = 0.30
                 setup.dmgain = 0.50
                 setup.utgain = 0.00
                 setup.dtsensor = 0
                 setup.lsltlson = 0
                 setup.aofotthr = 20.0
                 setup.lst3pcrg = 0
                 setup.stsetup = 0
                 setup.obsi = 0
                 setup.lbsetup = 0
                 setup.aottmode = 1
                 setup.aofomode = 1
                 setup.lst3pcre = 0
              end

              1:begin ;; ngs / lgs "engineering mode"
                 obsdnames = ['sodiumDichroic','beamSplitter']
                 XMESSAGE, 'Choose SOD optic:', obsdnames, aotsgold
                 setup.obsdname = obsdnames[aotsgold]
                 setup.obamname = 'mirror'
                 setup.obasname = 'ngs'
                 setup.obwnname = 'open'
                 setup.obwfdsrc = 0 ; manual
                 setup.obwpdsrc = 0 ; manual
                 setup.tssset = 1
                 setup.aofclgct = 0                 
                 setup.aofcosoc = 1 ; one shot mode
                 setup.aofctroc = 0
                 setup.aotsgold = FLOAT(aotsgold)
                 setup.guidwave = 0.68e-6
                 setup.dtgain = 0.2
                 setup.dmgain = 0.5
                 setup.utgain = 0.0
                 setup.dtsensor = 1
                 setup.lsltlson = 0
                 setup.aofotthr = 20.0
                 setup.lst3pcrg = 0
                 setup.stsetup = 1
                 setup.obsi = -1.5
                 setup.lbsetup = 1
                 setup.aottmode = 1
                 setup.aofomode = 1
                 setup.lst3pcre = 0
              end

              2:begin ;; purely lgs
                 setup.obsdname = 'sodiumDichroic'
                 setup.obamname = 'mirror'
                 setup.obasname = 'ngs'
                 setup.obwnname = 'open'
                 setup.obwfdsrc = 2 ; tracking
;; SCE. Adapted for CLS from K1FST                 
;;                 IF data.telescope EQ 'Keck I' THEN
                 setup.obwpdsrc = 0
;;                 ELSE setup.obwpdsrc = 2
;;                 ; tracking for KeckII  CRN make this 0 for keck I, SC might not have tracking WPS !!! 03may2012
; SR uncommented the following set of the setup commands
                 setup.tssset = 1
                 setup.aofclgct = 1
                 setup.aofcosoc = 0
                 setup.aofctroc = 1 ; tracking mode
                 setup.aotsgold = 0.
                 setup.guidwave = 0.68e-6
                 setup.dtgain = 0.2
                 setup.utgain = 0.10
                 setup.dmgain = 0.40
                 setup.dtsensor = 1
                 setup.lsltlson = 1
                 setup.aofotthr = 20.
                 setup.lst3pcrg = data.lst3pcrg
                 setup.stsetup = 1
                 setup.obsi = -1.5
                 setup.lbsetup = 1
                 setup.aottmode = 1
                 setup.aofomode = 0
                 setup.lst3pcre = 1
              end
           endcase
           
           data.obsdname=setup.obsdname
           
           dev = REPLICATE({root:'', name:'', slew:0B}, 7)
           dev.root = ['obsd', 'obam', 'obas', 'obfm', 'obts', 'obts', 'obwn']   ;replaced obsi with obts for temp K1 fix since sfd is currently inop
           dev.name = ['sod', 'afm', 'afs', 'fsm', 'tss', 'sfd', 'wnd']    
           dtsensors = ['WFS','STRAP']
           
;;; Let 'er rip!
           TQ, data, 'Opening all loops'
;; SCE. Adapted for CLS from K1FST                 
;;           CASE data.telescope OF
;;              'Keck I':  loops = ['ao.aoloop', 'ao.utlp','ao.aottmode', 'ao.aofomode','ao.lspntrce'] ;; CRN for FST
;;              ELSE: loops = ['ao.aoloop', 'ao.utlp','ao.aottmode', 'ao.aofomode', 'ao.lst3pcre']
;;           ENDCASE
           loops = ['ao.aoloop', 'ao.utlp','ao.aottmode', 'ao.aofomode','ao.lspntrce'] ;; Used for k1 and k2

           FOR n=0,N_ELEMENTS(loops)-1 DO status = MODIFY(loops[n],0,err=err,/notrace)

;; for "LASER ZENITH" set rotator to proper VA
           IF ( data.aoopsmode eq 2 && data.tname eq "LASER ZENITH" ) then begin
             ; Move rotator to VA=116.6
             rotdest = SHOW('dcs.rotdest',stat=stat,err=err,/notr)
             rotmode = SHOW('dcs.rotmode',stat=stat,err=err,/notr)
;; SCE. Adapted for CLS from K1FST                 
;             CASE data.telescope OF
;              'Keck I':begin
                 if (ABS(rotdest/!dtor- 0.0) gt 0.1) or (rotmode ne 2) then begin 
                   TQ, data, 'Setting rotator to VA=0.0'
                   tmp = MODIFY('dcs.rotdest',0.0*!dtor,stat=stat, $
                                 err=err, /notr)
                   tmp = MODIFY('dcs.rotmode',2,stat=stat,err=err,/notr)
                   ;dev[7].slew = 1
                 endif             
;;              endcase
;;              else:begin
;;                 if (ABS(rotdest/!dtor-116.6) gt 0.1) or (rotmode ne 2) then begin 
;;                   TQ, data, 'Setting rotator to VA=116.6'
;;                   tmp = MODIFY('dcs.rotdest',116.6*!dtor,stat=stat, $
;;                                 err=err, /notr)
;;                   tmp = MODIFY('dcs.rotmode',2,stat=stat,err=err,/notr)
;;                   ;dev[7].slew = 1
;;                 endif
;;               end
;;             endcase
           ENDIF
             
;; turn telemetry recording on if not already on
           trsrec=SHOW('ao.trsrec',/nowait,/notrace)
           IF data.simulate EQ 0 AND trsrec NE 7 THEN status=MODIFY('ao.trsrec',7,error=error,/notrace)
           
;; for all modes: 
           ;;set TT reference name on instrument
           TQ, data, 'Set AO ref. name for science inst.'
           ;; clean up *'s in target name (kwd compatibility)
           starpos = strpos(data.tname, '*')
           WHILE starpos NE -1 do begin
              tmp = data.tname
              strput, tmp, ' ', starpos 
              data.tname = tmp
              starpos = strpos(data.tname, '*')
           ENDWHILE
           
           IF data.instname EQ 'NIRC2' then begin
              TQ, data, 'update object name...'
              TQ, data, 'Connecting to nirc2server to'
              SPAWN, 'rsh waikoko -l nirc2eng object '+STRING(data.tname), tmp
           ENDIF
           
           tmp = MODIFY('ao.obptname', STRING(data.tname), stat=stat,err=err,/notrace)
           
           ;; reset LBWFS decount and LBWFS RMS WF
           tmp = MODIFY('ao.lbtmtocp', 0., status=status, error=err, /notrace)
           tmp =  MODIFY('ao.lgrmswf', 300.0, status=status, error=err, /notrace)
           
           obsdname = SHOW('ao.obsdname', stat=stat, err=err, /notrace)
           IF (obsdname NE setup.obsdname) THEN BEGIN
              TQ, data, 'Installing SOD ' + setup.obsdname
              tmp = MODIFY('ao.obsdname',setup.obsdname,stat=stat,err=err,/notrace)
              dev[0].slew = 1
           ENDIF

           obamname = SHOW('ao.obamname', stat=stat, err=err, /notrace)
           IF (obamname NE setup.obamname) THEN BEGIN
              TQ, data, 'Installing AFM ' + setup.obamname
              tmp = MODIFY('ao.obamname',setup.obamname,stat=stat,err=err,/notrace)
              dev[1].slew = 1
           ENDIF

           obasname = SHOW('ao.obasname', stat=stat, err=err, /notrace)
           IF (obasname NE setup.obasname) THEN BEGIN
              TQ, data, 'Moving AFS to named position ' + setup.obasname
              tmp = MODIFY('ao.obasname',setup.obasname,stat=stat,err=err,/notrace)
              dev[2].slew = 1
           ENDIF
           

; Close the WYKO shutter if not in simulate mode
;           ifwystat=SHOW('ao.ifwystat', status=status, error=err,/notrace) ; 1=closed, 2=open
;           CASE ifwystat OF
;              1: TQ,data, 'Wyko shutter is closed'
;              ELSE: BEGIN
;                 TQ,data, 'Wyko shutter is not closed'
;                 IF NOT data.simulate THEN BEGIN
;                    TQ,data, 'Closing Wyko shutter'
;                    tmp=MODIFY('ao.ifwyshtr', 0, status=status, error=err, /notrace) ; closed=0, open=1 !  
;                 ENDIF
;              END
;           ENDCASE           

; -- Liz here, 11/6/12 :           
; Close the WYKO shutter if not in simulate mode 
;
           aowykoshsts=SHOW('ao.aowykoshsts', status=status, error=err,/notrace)
;  		(readback: 0:invalid, 1:open, 2:closed, 3:moving) 
;
           CASE aowykoshsts OF
              2: TQ,data, 'Wyko shutter is closed'
              ELSE: BEGIN
                 TQ,data, 'Wyko shutter is not closed'
                 IF NOT data.simulate THEN BEGIN
                    TQ,data, 'Closing Wyko shutter'
;
;		     Command action: 0: Open, 1:close
;
                    tmp=MODIFY('ao.aowykoshcmd', 1, status=status, error=err, /notrace) 
                 ENDIF
              END
           ENDCASE           
           
           TQ, data, 'Configuring focus manager'
           tmp = MODIFY('ao.aofcosoc', setup.aofcosoc, stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aofctroc', setup.aofctroc, stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aofcngct', 1, stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aofclgct', setup.aofclgct, stat=stat,err=err,/notrace)
           tmp = MODIFY('ao.aofclbct', 0, stat=stat, err=err, /notrace)
           
           obwfdsrc = SHOW('ao.obwfdsrc', stat=stat, err=err, /notrace)
           IF (obwfdsrc NE setup.obwfdsrc) THEN BEGIN
              TQ, data, 'Switching FCS to tracking or manual'
              tmp = MODIFY('ao.obwfdsrc',setup.obwfdsrc , stat=stat, err=err, /notrace)
              tmp = MODIFY('ao.obwfmove', 1, stat=stat, err=err, /notrace)
           ENDIF
           
; set FCS C0
; make sure that right '-N' or '-L' or '' is loaded
           CASE setup.obsdname OF
              'sodiumDichroic': suffix='-L'
               ELSE: suffix='-N'
           ENDCASE
              
; set the FSMs for the instrument      
           path2cal='/kroot/rel/ao/qfix/data/'
           fname = path2cal+'fsm_origin.dat'
           fname_inst = fname+STRING(data.instname+suffix)
           MESSAGE,/INFO,'Copying '+fname_inst+' to '+fname 
           SPAWN, '\cp -p '+fname_inst+' '+fname, foo
           LOADFSMORI
              
           
; set the offsets for the sodium or beamsplitter           
; these values were derived experimentally as to where the best focus of the FCS appears to be on the sky (for some unexplained reason, this differs from the calibrated value). We don't know whether we have this problem on Keck I or not. If we ever fix this problem, then the offsets should be removed.
;; SCE. Adapted for CLS from K1FST                 
; S. Ragland uncommented the fcs offsets for Keck II           
           CASE data.telescope OF
              'Keck II': BEGIN
                 CASE suffix OF 
                    '-L': aofcc0so=-0.7
                    '-N': aofcc0so=-0.4
                 ENDCASE
                 IF data.simulate THEN aofcc0so=0.
                 status=MODIFY('ao.aofcc0so',FLOAT(aofcc0so),/notrace)
                 TQ,data,'Setting SOD FCS offset to '+STRING(aofcc0so,format='(f5.2)')
              END
              ELSE: begin
                 CASE suffix OF 
                    '-L': aofcc0so=0
                    '-N': aofcc0so=0
                 ENDCASE
                 IF data.simulate THEN aofcc0so=0.
                 status=MODIFY('ao.aofcc0so',FLOAT(aofcc0so),/notrace)
                 TQ,data,'Setting SOD FCS offset to '+STRING(aofcc0so,format='(f5.2)')
              END 
           ENDCASE
           
           TQ,data,'Setting FCS C0 for '+data.instname+suffix
           status=SET_FCS_FOR_INST(data.instname+suffix)
           
           obwpdsrc = SHOW('ao.obwpdsrc', stat=stat, err=err, /notrace)
           IF (obwpdsrc NE setup.obwpdsrc) THEN BEGIN
              TQ, data, 'Switching WPS to tracking or manual'
              tmp = MODIFY('ao.obwpdsrc', setup.obwpdsrc , stat=stat, err=err, /notrace)
              tmp = MODIFY('ao.obwpmove', 1 , stat=stat, err=err, /notrace)
           ENDIF
           
           IF data.aoopsmode NE 2 THEN temp=MODIFY('ao.obwpname', 'ngs', error=error,/notrace)
           
           IF data.darmode ge 0 THEN BEGIN
              TQ, data, 'Setting up DAR'
              tmp = MODIFY('dcs.guidwave', setup.guidwave,stat=stat,err=err,/notrace) 
              tmp = MODIFY('ao.aodrzsim', 1.0, stat=stat, err=err, /notrace)
              tmp = MODIFY('ao.aodrena', 1.0, stat=stat, err=err, /notrace)
              tmp = MODIFY('ao.aotfenb', 1, stat=stat, err=err, /notrace) ;TSSfoc              
           endif
           
           ;;; set up tss gold numbers
           aotsbsg = NAMEDPOSN(dev='tss', name='optbsstrap')
           aotssdg = NAMEDPOSN(dev='tss', name='optsodstrap')
           
           tmp = MODIFY('ao.aotsbsgx', -1*aotsbsg[0], stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aotsbsgy', -1*aotsbsg[1], stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aotsbsgz', -1*aotsbsg[2], stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aotssdgx', -1*aotssdg[0], stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aotssdgy', -1*aotssdg[1], stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aotssdgz', -1*aotssdg[2], stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aotsgold', setup.aotsgold, stat=stat,err=err,/notrace)             

;******************
; Branch on off axis logic, RDC, Feb 2012
;******************
           if (data.offAxisFlag) then begin
              getTTpnt,data
              if (setup.tssSet) then begin
;******************
; LGS mode: TSS to TT star offset coordinates, 
;           FSM to poining ref (typically sci camera)
;******************
                aots = data.pntTTcur
                obsdname = SHOW('ao.obsdname', stat=stat, err=err, /notrace)
                IF obsdname EQ 'sodiumDichroic' then $
                  obtsz = NAMEDPOSN(dev='tss', name='optsodstrap', axis='z') else $
                    obtsz = NAMEDPOSN(dev='tss', name='optbsstrap', axis='z')
                txt = 'Moving TSS to ' + $
                       STRING([aots,obtsz],f='(" X=",F7.3," Y=",F7.3," Z=",F6.3)')
                TQ, data, txt
              
                tmp = MODIFY('ao.aotsx', aots[0]*1e-3, stat=stat, err=err, /notrace)
                tmp = MODIFY('ao.aotsy', aots[1]*1e-3, stat=stat, err=err, /notrace)
                tmp = MODIFY('ao.aotsgo', 1, stat=stat, err=err, /notrace)
                dev[4].slew = 1
 
                aofm = data.pntrefcur
                txt = 'Moving FSMs to ' + STRING(aofm,f='(" X=",F6.3," Y=",F6.3)')
                TQ, data, txt
                tmp = MODIFY('ao.aofmx', aofm[0]*1e-3, stat=stat, err=err, /notrace)
                tmp = MODIFY('ao.aofmy', aofm[1]*1e-3, stat=stat, err=err, /notrace)
                tmp = MODIFY('ao.aofmgo', 1, stat=stat, err=err, /notrace)
                dev[3].slew = 1              
              endif  else begin         
;******************
; NGS mode, Move only FSMs to TT location
;******************
                aofm = data.pntTTcur
                txt = 'Moving FSMs to ' + STRING(aofm,f='(" X=",F6.3," Y=",F6.3)')
                TQ, data, txt
                tmp = MODIFY('ao.aofmx', aofm[0]*1e-3, stat=stat, err=err, /notrace)
                tmp = MODIFY('ao.aofmy', aofm[1]*1e-3, stat=stat, err=err, /notrace)
                tmp = MODIFY('ao.aofmgo', 1, stat=stat, err=err, /notrace)
                dev[3].slew = 1
              endelse             
;******************
;ON axis mode (same as before) RDC Feb 2012
;Moving FSM's to PO (note that fsmset is always true)
;******************
           endif else begin

           IF (setup.fsmset EQ 1) THEN BEGIN
              aofm = data.pntrefcur
              txt = 'Moving FSMs to ' + STRING(aofm,f='(" X=",F6.3," Y=",F6.3)')
              TQ, data, txt
              tmp = MODIFY('ao.aofmx', aofm[0]*1e-3, stat=stat, err=err, /notrace)
              tmp = MODIFY('ao.aofmy', aofm[1]*1e-3, stat=stat, err=err, /notrace)
              tmp = MODIFY('ao.aofmgo', 1, stat=stat, err=err, /notrace)
              dev[3].slew = 1
           ENDIF

           IF (setup.tssset EQ 1) THEN BEGIN
              aots = data.pntrefcur
              obsdname = SHOW('ao.obsdname', stat=stat, err=err, /notrace)
              IF obsdname EQ 'sodiumDichroic' then $
                 obtsz = NAMEDPOSN(dev='tss', name='optsodstrap', axis='z') else $
                    obtsz = NAMEDPOSN(dev='tss', name='optbsstrap', axis='z')
              txt = 'Moving TSS to ' + $
                    STRING([aots,obtsz],f='(" X=",F6.3," Y=",F6.3," Z=",F6.3)')
              TQ, data, txt
              
              tmp = MODIFY('ao.aotsx', aots[0]*1e-3, stat=stat, err=err, /notrace)
              tmp = MODIFY('ao.aotsy', aots[1]*1e-3, stat=stat, err=err, /notrace)
              tmp = MODIFY('ao.aotsgo', 1, stat=stat, err=err, /notrace)

              dev[4].slew = 1
           ENDIF
        endelse
           
;;           IF data.telescope EQ 'Keck II' THEN BEGIN
              lsltlson = SHOW('ao.lsltlson', stat=stat, err=err, /notrace)
              IF (lsltlson NE setup.lsltlson) THEN BEGIN
                 TQ, data, 'Switching LTCS laser configuration ' + dtsensors[setup.dtsensor]
                 tmp = MODIFY('ao.lsltlson', setup.lsltlson,stat=stat,err=err,/notrace)
              ENDIF
;;           ENDIF           
           
           IF (setup.aofotthr NE 0.) THEN BEGIN
              aofotthr = SHOW('ao.aofotthr', stat=stat, err=err, /notrace)
              IF aofotthr NE setup.aofotthr THEN BEGIN
                 TQ, data, 'Setting WFO period to '+STRTRIM(setup.aofotthr,2) + 's'
                 tmp = MODIFY('ao.aofotthr',setup.aofotthr,stat=stat,err=err,/notrace)
              ENDIF
           ENDIF

;; SCE. Adapted for CLS from K1FST                 
           IF (setup.lst3pcrg NE 0.) THEN BEGIN
;;              IF data.telescope EQ 'Keck II' THEN BEGIN
;;                 TQ, data, 'Configuring M3 integrator'
;;                 tmp = MODIFY('ao.lst3pcrg',setup.lst3pcrg,stat=stat,err=err,/notrace)
;;                 tmp = MODIFY('ao.lst3pcri',1,stat=stat,err=err,/notrace) ; zero it
;;              ENDIF ELSE BEGIN 
                 TQ, data, 'Configuring M2-M5 integrator'  ;; CRN changes for FST just zero, leave gain as set by FST system startup
                 tmp = MODIFY('ao.lspntrci',1,stat=stat,err=err,/notrace) ; zero integrator
;;              ENDELSE
           ENDIF
           
           dtsensor = SHOW('ao.dtsensor', stat=stat, err=err, /notrace)
           IF (dtsensor NE setup.dtsensor) THEN BEGIN
              TQ, data, 'Switching DT sensor to ' + dtsensors[setup.dtsensor]
              tmp = MODIFY('ao.dtsensor', setup.dtsensor,stat=stat,err=err,/notrace)
              WAIT,1
           ENDIF
           
           data.setuprmag=data.rmag           
; determine the STRAP and WFS equivalent magnitudes 
           data.wfsrmag=EFFECTIVERMAG(data.rmag,aoopsmode=data.aoopsmode,obsdname=data.obsdname)
           data.straprmag=EFFECTIVERMAG(data.rmag,aoopsmode=data.aoopsmode,obsdname=data.obsdname,/strap)
           
           IF (setup.stsetup EQ 1) THEN BEGIN               
              TQ, data, 'Setting STRAP for effective mR='+STRTRIM(STRING(data.straprmag,f='(F5.1)'),2)
              SETUP_STRAP, data.straprmag, status=status
              IF status EQ -1 THEN BEGIN
                 tmp=DIALOG_MESSAGE('Strap settings not defined for this magnitude',/error)
                 TQ,data,'Strap settings not defined for this magnitude'
                 data.status[0:2] = [1,1,1]
                 AOACQ_STATUS, data
                 RETURN
              ENDIF              
           ENDIF ELSE BEGIN
                 ststate = SHOW('ao.ststate', stat=stat, err=err, /notrace)
                 IF ststate NE 0 then tmp = MODIFY('ao.ststby', 1, stat=stat, err=err, /notrace)
                 obswname = SHOW('ao.obswname', stat=stat, err=err, /notrace)
                 IF (obswname NE 'BLOCK') then tmp = MODIFY('ao.obswname', 'block', stat=stat, err=err, /notrace)
              
           ENDELSE
           
           IF (setup.obsi NE 0.) THEN BEGIN
              obsi = SHOW('ao.obsi', stat=stat, err=err, /notrace)*1e3
              IF (ABS(obsi-setup.obsi) gt 0.01) THEN BEGIN
                 tmp = MODIFY('ao.obsi', setup.obsi*1e-3, stat=stat,err=err,/notrace)
                 dev[5].slew = 1
              ENDIF
           ENDIF
           
           TQ, data, 'Halting LBWFS'
           tmp = MODIFY('ao.aolbloop', 0, stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aolblpstr', 'Halted' , stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.lblpnfra', 0, stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aolbsvcg', 0, stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.aofclbct', 0, stat=stat, err=err, /notrace)
           tmp = MODIFY('ao.lbtmtocp', 0., status=status, error=err, /notrace)
           
           txt = 'Closing TTO'
           IF (setup.aofomode EQ 1) then txt = txt + ', WFO'
;; SCE. Adapted for CLS from K1FST                 
           IF (setup.lst3pcre EQ 1) then txt = txt + ', M2-M5' ;; CRN for FST
;;           CASE data.telescope OF
;;              'Keck I':  IF (setup.lst3pcre EQ 1) then txt = txt + ', M2-M5' ;; CRN for FST
;;              ELSE: IF (setup.lst3pcre EQ 1) then txt = txt + ', M3'
;;           ENDCASE

           TQ, data, txt + ' offload loops'
           tmp = MODIFY('ao.aottmode', setup.aottmode, stat=stat, err=err, /notrace)
           IF (setup.aofomode NE 0) then $
              tmp = MODIFY('ao.aofomode', setup.aofomode, stat=stat,err=err,/notrace)
           IF (setup.lst3pcre NE 0) then begin 
;; SCE. Adapted for CLS from K1FST                 
              tmp = MODIFY('ao.lspntrce', setup.lst3pcre, stat=stat,err=err,/notrace)  ;; CRN for FST
;;             CASE data.telescope OF
;;                'Keck I': tmp = MODIFY('ao.lspntrce', setup.lst3pcre, stat=stat,err=err,/notrace)  ;; CRN for FST
;;                ELSE: tmp = MODIFY('ao.lst3pcre', setup.lst3pcre, stat=stat,err=err,/notrace)
;;             ENDCASE

           ENDIF
           WHILE (MAX(dev.slew) EQ 1) do begin
              idx = WHERE(dev.slew EQ 1, ns)
              fmt = '(' + STRTRIM(ns,2) + '(A,X))'
              TQ, data, 'Waiting for ' + STRING(dev[idx].name,f=fmt)
              AOACQ_PLOT, data
              WAIT,2
              for i=0,ns-1 do begin
                 stst = SHOW('ao.'+dev[idx[i]].root+'stst',stat=stat,err=err,/notrace)
                 dev[idx[i]].slew = (stst NE 'INPOS')
              endfor
           ENDWHILE
           
           recapsmt='236'       ; can make this telescope/plate scale dependent
           status=MODIFY('ao.recapsmt',recapsmt,/notrace)
           
; turn off DTT and UTT dithering
           dtdst=SHOW('ao.dtdst',/notrace,/nowait)
           IF dtdst EQ 1 THEN status=MODIFY('ao.dtdst',0,error=error,/notrace)
           
           utdst=SHOW('ao.utdst',/notrace,/nowait)
           IF utdst EQ 1 THEN status=MODIFY('ao.utdst',0,error=error,/notrace)
           
; if loading a saved configuration, we are all done
           IF data.archmode NE 0 THEN RETURN
           
; set up the servos, gains
           status=MODIFY('ao.dtservo',[1D,0,0,0,-1,0,0],error=error,/notrace) 
           status=MODIFY('ao.utservo',[1D,0,0,0,-1,0,0],error=error,/notrace) 
           status=MODIFY('ao.dmservo',[1D,0,0,0,-0.99,0,0],error=error,/notrace) 
           status=MODIFY('ao.dtclp',1,error=error,/notrace) ; close the DTT CLMP loop 
;; SCE. Adapted for CLS from K1FST                 
;;           IF data.telescope EQ 'Keck II' THEN BEGIN
;;              status=MODIFY('ao.utclp',0,error=error,/notrace) ; open the UTT CLMP loop 
;;           ENDIF ELSE BEGIN
              status=MODIFY('ao.utclp',1,error=error,/notrace) ; close the UTT CLMP loop CRN FST change 20Apr2012
;;           ENDELSE
           status=MODIFY('ao.dtgain',setup.dtgain,error=error,/notrace)
           status=MODIFY('ao.dmgain',setup.dmgain,error=error,/notrace)
           status=MODIFY('ao.utgain',setup.utgain,error=error,/notrace)
           
           IF data.aoopsmode EQ 2 THEN BEGIN
              obpsxfs=0
              SETFRAMERATE,data.lgsfrrt,prog=2
              
              obwnname = SHOW('ao.obwnname', stat=stat, err=err, /notrace)              
              IF (obwnname NE setup.obwnname) THEN BEGIN
                 TQ, data, 'Moving WND to named position ' + setup.obwnname
                 tmp = MODIFY('ao.obwnname',setup.obwnname,stat=stat,err=err,/notrace)
                 dev[6].slew = 1
              ENDIF
              
              binning=2
              prefix='24'
              data.guidestar='LGS'
              WIDGET_CONTROL,data.drp_id[20],set_val='LGS' 
           ENDIF ELSE BEGIN
              
; need to set the plate scale here depending on the observation     
              IF data.instname EQ 'IF' or data.instname EQ 'ASTRA' or data.instname EQ 'OHANA' THEN BEGIN
                 obpsxfs=SHOW('ao.obpsxfs',error=error,status=status,/notrace)
                 IF obpsxfs EQ 3 THEN binning=1 ELSE binning=2
                 
                 wssmbin=SHOW('ao.wssmbin',error=error,status=status,/notrace)
                 IF wssmbin NE binning THEN BEGIN
                    TQ,data, 'Changing binning mode'
                    wsfrrt=SHOW('ao.wsfrrt',error=error,status=status,/notrace)
                    SETFRAMERATE,wsfrrt,binning=binning
                 ENDIF
                 
              ENDIF ELSE BEGIN  ; could set different plate scales for different objects
                 obpsxfs=0 
              ENDELSE
              
; Determine what the AO settings should be as a function of magnitude          
              TQ,data,'Setting WFS for effective mR='+STRTRIM(STRING(data.wfsrmag,f='(F5.1)'),2)
              data.watao = SETNGSAO_VMAG(data.wfsrmag,bkgnd=wfbkgnd) ; watao (what AO settings?) variable traces the status of the AO config
              data.wfbkgnd=wfbkgnd
              
              IF (data.watao EQ -1) THEN BEGIN
                 txt = '****Warning****                 \' + $
                       ' The AO settings are wrong      \' + $
                       ' Check the Rmag and B-Vmag      \'
                 XMESSAGE,txt,['OK'],retval 
                 RETURN
              ENDIF    
              
              obpsxfs=SHOW('ao.obpsxfs',error=error,status=status,/notrace)
              
              CASE obpsxfs OF
                 2:  prefix='10'
                 3:  prefix='06'
                 ELSE: prefix='24'
              ENDCASE
              
              binning=SHOW('ao.wssmbin',error=error,status=status,/notrace)
              IF status LT 0 THEN BEGIN
                 MESSAGE,/INFO,'Cannot read the binning keyword, ao.wssmbin'
                 TQ,data,'Cannot read the binning keyword, ao.wssmbin'
                 binning=2
              ENDIF
           ENDELSE
           
           status=MODIFY('ao.obpsxfs',obpsxfs,/notrace)
           WAIT,0.20
           TQ,data,'Setting up the lenslet config'
           WFSCONFIG
           
; update the centroid gain           
           UPDATE_CENTROID_GAIN,data
           
           binning=STRING(binning,format='(i1)')  
           binstring=binning+'x'+binning
           cogfn=prefix+data.instname+suffix+binstring+'.cog'
           TQ,data,'Loading cog file '+cogfn
           LOADCOG,cogfn
           
           data.status[0:2] = [3,1,1]
           AOACQ_STATUS, data
           TQ, data, 'Bench setup done'
           WIDGET_CONTROL,event.top,set_uvalue=data
        end

        'setup_bench_help':begin
           txt = 'SETUP BENCH\' + $
                 '                                                  \' + $
                 '[only some AO modes]\' + $
                 '1) open all loops.                                \' + $
                 '2) set SOD, AFM, AFS, [TSS].                      \' + $
                 '3) switch FCS, WPS to tracking.                   \' + $
                 '4) Configure focus manager.                       \' + $
                 '5) Configure DAR.                                 \' + $
                 '6) Send FSMs to reference position.               \' + $
                 '7) [Send TSS to reference position.]              \' + $
                 '8) Load default cog file.                         \' + $
                 '9) Set appropriate reconstructor & gains.         \' + $
                 '10) Set dtsensor.                                 \' + $
                 '11) [Reset FO period to 20s.]                     \' + $
                 '12) [Setup and zero M3 integrator.]               \' + $
                 '13) [Setup STRAP and LBWFS.]                      \' + $
                 '14) Close TTO, [WFO, M3] offload loops.           \' + $
                 '15) Wait for stages to finish slewing.            '
           XMESSAGE, txt, 'OK', foo
        end





