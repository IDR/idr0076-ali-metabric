BEGIN;
CREATE TEMPORARY VIEW masks AS
SELECT i.id, count(r.id) as masks
  FROM roi r, shape m, image i, datasetimagelink dil
 WHERE dil.parent = 11000 and dil.child = i.id and i.id = r.image and r.id = m.roi and m.discriminator = 'mask'
 GROUP BY i.id;

  with mask_stats as (
      select min(masks) as min,
  	   max(masks) as max
        from masks
  ),
       histogram as (
     select width_bucket(masks, min, max, 12) as bucket,
  	  min(masks) as min, max(masks) as max,
  	  count(*) as freq
       from masks, mask_stats
   group by bucket
   order by bucket
  )
   select bucket, min, max, freq,
  	repeat('■',
  	       (   freq::float
  		 / max(freq) over()
  		 * 30
  	       )::int
  	) as bar
     from histogram;

  select sum(masks) as total from masks;
  
  ROLLBACK;
