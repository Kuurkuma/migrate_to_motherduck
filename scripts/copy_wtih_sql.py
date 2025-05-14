import duckdb

con = duckdb.connect("md:big_query_migration")

# install & load duckdb extensions
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("INSTALL parquet; LOAD parquet;")

files_tuples = con.execute(
    "FROM GLOB('gs://bq_migration_eth_dataset/*.parquet');"
).fetchall()

if not files_tuples:
    print("No Parquet files found.")
else:
    print(f"Found {len(files_tuples)} Parquet files.")
    # print(files_tuples) # files_tuples will be like [('path1',), ('path2',)]

    # Step 2: Break into chunks
    chunk_size = 100
    chunks = [files_tuples[i:i+chunk_size] for i in range(0, len(files_tuples), chunk_size)]

    # Step 3: Loop over chunks and append to a table
    for i, chunk in enumerate(chunks):
        file_list_str = ", ".join([f"'{f[0]}'" for f in chunk])
        sql = f"""
            INSERT INTO eth_table
            SELECT * FROM read_parquet([{file_list_str}]);
        """ if i > 0 else f"""
            CREATE OR REPLACE TABLE eth_table AS
            SELECT * FROM read_parquet([{file_list_str}]);
        """
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        con.execute(sql)
    print("Processing complete.")

con.close()
 
