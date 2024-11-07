COPY (SELECT DISTINCT 
  'FlyBase:'||a.uniquename AS allele_id,
  string_agg(DISTINCT a.name, '|') AS allele_name, 
  string_agg(DISTINCT s.name, '|') AS allele_synonyms
-- features linked to expression statements
FROM feature_expression fe 
JOIN feature f ON fe.feature_id = f.feature_id AND f.is_obsolete='f'
-- alleles linked to these features
JOIN feature_relationship fr ON fr.subject_id = f.feature_id
JOIN cvterm r ON fr.type_id = r.cvterm_id AND r.name IN ('associated_with') 
JOIN feature a ON fr.object_id = a.feature_id AND a.uniquename LIKE 'FBal%' AND a.is_obsolete='f'
-- get synonyms
LEFT JOIN feature_synonym fs ON a.feature_id=fs.feature_id
LEFT JOIN synonym s ON fs.synonym_id=s.synonym_id
GROUP BY allele_id
) TO STDOUT WITH DELIMITER E'\t' CSV HEADER;