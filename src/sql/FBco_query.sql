COPY (SELECT DISTINCT 
  'FlyBase:'||s.uniquename AS combo_id,
  string_agg(DISTINCT s.name, '|') AS combo_name, 
  string_agg(DISTINCT ss.name, '|') AS combo_synonyms, 
  'FlyBase:'||o.uniquename AS allele_id,
  string_agg(DISTINCT o.name, '|') AS allele_name, 
  string_agg(DISTINCT os.name, '|') AS allele_synonyms, 
  string_agg(DISTINCT 'FlyBase:'||direct_tools.tool_id, '|') AS direct_tool_id, 
  string_agg(DISTINCT 'FBcv:'||direct_tools.tool_cv_acc, '|') AS direct_tool_fbcv,
  string_agg(DISTINCT 'FlyBase:'||indirect_tools.tool_id, '|') AS indirect_tool_id, 
  string_agg(DISTINCT 'FBcv:'||indirect_tools.tool_cv_acc, '|') AS indirect_tool_fbcv

-- first get all FBcos and associated alleles
  FROM feature s 
    JOIN feature_relationship fr ON fr.subject_id=s.feature_id
    JOIN cvterm r ON fr.type_id=r.cvterm_id
    JOIN feature o ON fr.object_id=o.feature_id
    LEFT JOIN feature_synonym sfs ON s.feature_id=sfs.feature_id
    LEFT JOIN synonym ss ON sfs.synonym_id=ss.synonym_id
    LEFT JOIN feature_synonym ofs ON o.feature_id=ofs.feature_id
    LEFT JOIN synonym os ON ofs.synonym_id=os.synonym_id

-- *** get FBtos linked directly to alleles ***
    LEFT JOIN (
      SELECT fr2.subject_id AS rel_id, t.uniquename AS tool_id, dx.accession AS tool_cv_acc
      FROM feature_relationship fr2
      JOIN feature t ON t.feature_id=fr2.object_id
      JOIN cvterm tr ON tr.cvterm_id=fr2.type_id
-- get FBcv annotations of direct tools
      JOIN feature_cvterm fc ON fc.feature_id=t.feature_id
      JOIN cvterm ct ON fc.cvterm_id=ct.cvterm_id
      JOIN cv c ON ct.cv_id=c.cv_id
      JOIN dbxref dx ON ct.dbxref_id=dx.dbxref_id
      JOIN db d ON dx.db_id=d.db_id
-- conditions
      WHERE t.uniquename ~ 'FBto.+'
      AND t.is_obsolete='f'
      AND tr.name IN ('encodes_tool', 'carries_tool', 'tagged_with', 'has_reg_region')
      AND d.name='FBcv'
    ) AS direct_tools ON direct_tools.rel_id=o.feature_id

-- *** get FBtos linked indirectly to alleles ***
    LEFT JOIN (
      SELECT fri.subject_id AS rel_id, t.uniquename AS tool_id, dx.accession AS tool_cv_acc
      FROM feature_relationship fri
      JOIN cvterm ci ON fri.type_id=ci.cvterm_id
      JOIN feature i ON i.feature_id=fri.object_id
      JOIN feature_relationship frp ON frp.subject_id=i.feature_id
      JOIN cvterm cp ON frp.type_id=cp.cvterm_id
      JOIN feature p ON p.feature_id=frp.object_id
      JOIN feature_relationship frt ON frt.subject_id=p.feature_id
      JOIN feature t ON t.feature_id=frt.object_id
      JOIN cvterm tr ON tr.cvterm_id=frt.type_id
-- get FBcv annotations of indirect tools
      JOIN feature_cvterm fc ON fc.feature_id=t.feature_id
      JOIN cvterm ct ON fc.cvterm_id=ct.cvterm_id
      JOIN cv c ON ct.cv_id=c.cv_id
      JOIN dbxref dx ON ct.dbxref_id=dx.dbxref_id
      JOIN db d ON dx.db_id=d.db_id
-- conditions
      WHERE ci.name='associated_with'
      AND cp.name='producedby'
      AND t.uniquename ~ 'FBto.+'
      AND t.is_obsolete='f'
      AND tr.name IN ('encodes_tool', 'carries_tool', 'tagged_with', 'has_reg_region')
      AND d.name='FBcv'
    ) AS indirect_tools ON indirect_tools.rel_id=o.feature_id

-- conditions
  WHERE o.uniquename ~ 'FBal.+'
  AND s.uniquename ~ 'FBco.+'
  AND r.name='partially_produced_by'
  AND o.is_obsolete='f'
  AND s.is_obsolete='f'

GROUP BY s.uniquename, o.uniquename
) TO STDOUT WITH DELIMITER E'\t' CSV HEADER;