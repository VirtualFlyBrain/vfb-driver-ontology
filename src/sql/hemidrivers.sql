COPY (SELECT DISTINCT 
  string_agg(DISTINCT split_tools.tool_FBcv, '|') AS tool_FBcv, 
  split_features.feature_FBid, 
  string_agg(DISTINCT split_features.feature_name, '|') AS feature_name, 
  string_agg(DISTINCT split_features.feature_synonym, '|') AS feature_synonyms, 
  split_feature_descendants.descendant_FBid, 
  string_agg(DISTINCT split_feature_descendants.descendant_name, '|') AS descendant_name, 
  string_agg(DISTINCT split_feature_descendants.descendant_synonym, '|') AS descendant_synonyms,
  split_feature_descendants2.descendant2_FBid, 
  string_agg(DISTINCT split_feature_descendants2.descendant2_name, '|') AS descendant2_name, 
  string_agg(DISTINCT split_feature_descendants2.descendant2_synonym, '|') AS descendant2_synonyms
FROM (SELECT f.uniquename AS tool_FBid, f.feature_id AS tool_id, d.name||':'||dx.accession AS tool_FBcv
FROM feature f
JOIN feature_cvterm fc ON fc.feature_id=f.feature_id
JOIN cvterm ct ON fc.cvterm_id=ct.cvterm_id
JOIN cv c ON ct.cv_id=c.cv_id
JOIN dbxref dx ON ct.dbxref_id=dx.dbxref_id
JOIN db d ON dx.db_id=d.db_id
WHERE d.name in ('FBcv')
AND dx.accession in ('0005055', '0005054')
AND f.is_obsolete='f') AS split_tools
JOIN (SELECT f.uniquename AS feature_FBid, f.name AS feature_name, s.name AS feature_synonym, f.feature_id, fr.object_id AS tool_id, cv.name AS relationship
FROM feature_relationship fr
JOIN feature f ON f.feature_id=fr.subject_id
JOIN cvterm cv ON cv.cvterm_id=fr.type_id
LEFT JOIN feature_synonym fs ON f.feature_id=fs.feature_id
LEFT JOIN synonym s ON fs.synonym_id=s.synonym_id
WHERE cv.name IN ('encodes_tool', 'alleleof', 'tagged_with'))
AS split_features
ON split_tools.tool_id=split_features.tool_id
LEFT JOIN (SELECT f.uniquename AS descendant_FBid, f.name AS descendant_name, s.name AS descendant_synonym, cv.name AS relationship, fr.object_id
FROM feature_relationship fr 
JOIN feature f ON f.feature_id=fr.subject_id
JOIN cvterm cv ON cv.cvterm_id=fr.type_id
LEFT JOIN feature_synonym fs ON f.feature_id=fs.feature_id
LEFT JOIN synonym s ON fs.synonym_id=s.synonym_id
WHERE cv.name IN ('associated_allele', 'producedby')
AND f.is_obsolete='f')
AS split_feature_descendants
ON split_features.feature_id=split_feature_descendants.object_id
LEFT JOIN (SELECT f.uniquename AS descendant2_FBid, f.name AS descendant2_name, s.name AS descendant2_synonym, cv.name AS relationship2, fr.subject_id
FROM feature_relationship fr 
JOIN feature f ON f.feature_id=fr.object_id
JOIN cvterm cv ON cv.cvterm_id=fr.type_id
LEFT JOIN feature_synonym fs ON f.feature_id=fs.feature_id
LEFT JOIN synonym s ON fs.synonym_id=s.synonym_id
WHERE cv.name IN ('associated_with', 'producedby')
AND f.is_obsolete='f')
AS split_feature_descendants2
ON split_features.feature_id=split_feature_descendants2.subject_id
GROUP BY split_feature_descendants.descendant_FBid, split_feature_descendants2.descendant2_FBid, split_features.feature_FBid
) TO STDOUT WITH DELIMITER E'\t' CSV HEADER;