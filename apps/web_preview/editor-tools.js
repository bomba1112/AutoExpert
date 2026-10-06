// Protected editorial operations; JSON inputs mirror the documented import contracts.
import {api, privateImageUrl} from './api.js?v=0.12.0';

export function editorTools(data,l,esc) {
  return `<section class="catalog-card"><h2>${esc(l('ownershipImport'))}</h2><p>${esc(l('ownershipImportHelp'))}</p><button class="button secondary full" data-editor="ownership-contracts">${esc(l('ownershipContracts'))}</button></section>`+rightsTools(l,esc)+curationTools(l,esc)+`<section class="catalog-card"><h2>${esc(l('assetUpload'))}</h2><form id="editor-asset-form"><label>${esc(l('assetMetadata'))}<textarea name="metadata" rows="8" required spellcheck="false">${esc(JSON.stringify({variant_ids:[],make:'',model:'',source_url:'',rights_reference:'',generated:false,commercial_reuse:false,generation:'',facelift:null,body:'',market:'',year_from:2020,year_to:2020},null,2))}</textarea></label><input type="file" name="image" accept="image/png,image/jpeg,image/webp" required><button class="button primary full">${esc(l('assetUpload'))}</button></form>${data.assets.map(a=>`<article class="asset-review" data-id="${esc(a.id)}"><p>${esc(a.id)} · ${esc(a.state)}</p><button class="button secondary" data-editor="preview" data-id="${esc(a.id)}">${esc(l('assetPreview'))}</button><div class="asset-review-image"></div><label>${esc(l('note'))}<textarea class="asset-review-note" minlength="10" required></textarea></label>${['approve','reject'].map(action=>`<button class="button secondary" data-editor="${action}" data-id="${esc(a.id)}">${esc(l(action))}</button>`).join('')}</article>`).join('')}</section><section class="catalog-card"><h2>${esc(l('battles'))}</h2><form id="editor-publication-form"><label>${esc(l('publicationJson'))}<textarea name="publication" rows="8" required spellcheck="false"></textarea></label><button class="button primary full">${esc(l('draft'))}</button><output class="publication-output"></output></form><form id="editor-publish-form"><label>${esc(l('publicationId'))}<input name="id" required></label><label>${esc(l('note'))}<textarea name="note" minlength="10" required></textarea></label><button class="button secondary full">${esc(l('publishEditorial'))}</button></form></section>`;
}

export function bindEditorTools(root,{refresh,fail,l}) {
  const previews = new Set();
  root.addEventListener('click',event=>{
    const target=event.target.closest('[data-editor]');if(!target||target.disabled)return;event.preventDefault();target.disabled=true;
    void(async()=>{
      if(target.dataset.editor==='ownership-contracts'){const r=await api('/knowledge/admin/ownership/contracts');const a=document.createElement('a');const url=URL.createObjectURL(new Blob([JSON.stringify(r,null,2)],{type:'application/json'}));a.href=url;a.download='ownership-import-contracts.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return;}
      if(target.dataset.editor==='load-variant'){const form=target.closest('form');const id=form.elements.variant.value;const d=await api('/knowledge/admin/variants/'+encodeURIComponent(id));form.elements.record.value=JSON.stringify(d.record,null,2);return;}
      const row=target.closest('.asset-review');
      if(target.dataset.editor==='preview'){
        for(const url of previews) URL.revokeObjectURL(url);previews.clear();
        const url=await privateImageUrl(`/knowledge/admin/assets/${target.dataset.id}/preview`);previews.add(url);
        const image=document.createElement('img');image.src=url;image.alt=l('assetPreview');image.style.maxWidth='100%';row.querySelector('.asset-review-image').replaceChildren(image);return;
      }
      const input=row.querySelector('.asset-review-note');if(!input.reportValidity())return;
      await api(`/knowledge/admin/assets/${target.dataset.id}/review`,{method:'POST',body:JSON.stringify({action:target.dataset.editor,note:input.value})});await refresh();
    })().catch(fail).finally(()=>{target.disabled=false;});
  });
  root.addEventListener('submit',event=>{
    const form=event.target;if(!['editor-asset-form','editor-publication-form','editor-publish-form','editor-curation-form','editor-variant-review','editor-rights-form'].includes(form.id))return;event.preventDefault();const submit=event.submitter;submit.disabled=true;
    void(async()=>{
      const fields=new FormData(form);
      if(form.id==='editor-rights-form'){await api('/knowledge/admin/sources/'+encodeURIComponent(fields.get('source_id')),{method:'PATCH',body:JSON.stringify({paused:fields.has('paused'),commercial_reuse:fields.has('commercial_reuse'),rights_reference:fields.get('rights_reference'),note:fields.get('note')})});await refresh();
      }else if(form.id==='editor-curation-form'){const r=await api('/knowledge/admin/variants/'+encodeURIComponent(fields.get('variant'))+'/draft',{method:'POST',body:JSON.stringify(JSON.parse(fields.get('record')))});form.querySelector('output').textContent=r.job_id+' · '+r.state;
      }else if(form.id==='editor-variant-review'){await api('/knowledge/admin/variants/'+encodeURIComponent(fields.get('variant'))+'/review',{method:'POST',body:JSON.stringify({action:submit.value,note:fields.get('note')})});await refresh();
      }else if(form.id==='editor-asset-form'){
        const metadata=JSON.parse(fields.get('metadata'));const file=fields.get('image');await api('/knowledge/admin/assets?metadata='+encodeURIComponent(JSON.stringify(metadata)),{method:'POST',headers:{'Content-Type':file.type},body:file});await refresh();
      }else if(form.id==='editor-publication-form'){
        const result=await api('/knowledge/admin/publications',{method:'POST',body:JSON.stringify(JSON.parse(fields.get('publication')))});form.querySelector('.publication-output').textContent=l('publicationId')+': '+result.id;
      }else{
        await api('/knowledge/admin/publications/'+encodeURIComponent(fields.get('id'))+'/review',{method:'POST',body:JSON.stringify({action:'publish',note:fields.get('note')})});await refresh();
      }
    })().catch(fail).finally(()=>{submit.disabled=false;});
  });
}

function curationTools(l,esc){return `<section class="catalog-card"><h2>${esc(l('curate'))}</h2><form id="editor-curation-form"><label>${esc(l('variantId'))}<input name="variant" required></label><button type="button" class="button secondary" data-editor="load-variant">${esc(l('loadRecord'))}</button><label>${esc(l('correction'))}<textarea name="record" rows="10" required spellcheck="false"></textarea></label><button class="button primary full">${esc(l('stageCorrection'))}</button><output></output></form><form id="editor-variant-review"><label>${esc(l('variantId'))}<input name="variant" required></label><label>${esc(l('note'))}<textarea name="note" minlength="10" required></textarea></label>${['lock','unlock','rollback'].map(a=>`<button class="button secondary" value="${a}">${esc(l(a))}</button>`).join('')}</form></section>`;}

function rightsTools(l,esc){return `<section class="catalog-card"><h2>${esc(l('rightsForm'))}</h2><form id="editor-rights-form"><label>${esc(l('sourceId'))}<input name="source_id" required></label><label>${esc(l('rightsReference'))}<textarea name="rights_reference" minlength="10" required></textarea></label><label class="check-label"><input type="checkbox" name="commercial_reuse">${esc(l('rightsConfirm'))}</label><label class="check-label"><input type="checkbox" name="paused">${esc(l('sourcePaused'))}</label><label>${esc(l('note'))}<textarea name="note" minlength="10" required></textarea></label><button class="button primary full">${esc(l('saveRights'))}</button></form></section>`;}
