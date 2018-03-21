def harvest_arxiv(id_list=False):
    "Gets metadata for latest submissions from the arXiv API or for the specified IDs."
    
    import urllib
    import feedparser
    
    base_url = 'http://export.arxiv.org/api/query?' # base api query url

    # search parameters
    start_index = 0               # 0 = most recent API result
    max_index = 1000              # upper bound on paper index we will fetch
    results_per_iteration = 100   # passed to arxiv API
    sort_by = 'submittedDate'   # submittedDate, lastUpdatedDate, relevance
    # ISSUE: sortBy does not work!!!
    

    # query used for arxiv API

    # alternative or additional to the search_query
    if id_list:
    	# note: if (except for id_list) no arguments specified, defaults to start=0 and max_results=10
    	query = 'id_list=%s&start=%i&max_results=%i' % (id_list,start_index,results_per_iteration)
    else:
    	# for documentation see https://arxiv.org/help/api/user-manual#detailed_examples
    	search_query = ('%28cat:cond-mat.dis-nn+OR+'
                'cat:cond-mat.stat-mech+OR+'
                'cat:cond-mat.str-el+OR+'
                'cat:physics.comp-ph+OR+'
                'cat:quant-ph%29'
                '+AND+'
                '%28cat:cs.LG+OR+'
                'cat:stat.ML%29')
    
    	query = 'search_query=%s&sortBy=%s&start=%i&max_results=%i' % (search_query, 
                                                               sort_by,
                                                               start_index, 
                                                               results_per_iteration)
    
    response = urllib.urlopen(base_url+query).read() # perform a GET request using the base_url and query
    afp = feedparser.parse(response) # parse the response using feedparser
    
    # print out feed information
    print 'Feed title:\n"%s"\n' % afp.feed.title
    print 'Feed last updated:\n%s\n' % afp.feed.updated
    # print opensearch metadata
    print 'Total Results for this query: %s' % afp.feed.opensearch_totalresults
    print 'Items Per Page for this query: %s' % afp.feed.opensearch_itemsperpage
    print 'Start Index for this query: %s'   % afp.feed.opensearch_startindex

    return afp

def list_all(afp):
    "List all findings for review with index, title, publication date and tags."

    index = 0
    for entry in afp.entries:
        print '\n %i'%(index)
        index = index+1
        print entry.title
        print '%i-%i-%i'%(entry.published_parsed.tm_mday, entry.published_parsed.tm_mon, entry.published_parsed.tm_year)
        all_cats = [tag['term'] for tag in entry.tags]
        print (' - ').join(all_cats)

def show_info(afp, index, title=True, summary=True, authors=True, pubdate=False, tags=False):
    "Display title, abstract and authors for a given paper from afp."
    entry = afp.entries[index]
    if title:
        print entry.title+'\n'
    if summary:
        print entry.summary+'\n'
    if authors:
        print (', ').join(author.name for author in entry.authors)
    if pubdate:
        print '%i-%i-%i'%(entry.published_parsed.tm_mday, entry.published_parsed.tm_mon, entry.published_parsed.tm_year)
    if tags:
        all_cats = [tag['term'] for tag in entry.tags]
        print (' - ').join(all_cats)

def formatted_block(afp, indices):
    "For given afp entry indices, makes formatted entries and concats them in one string."

    formatted_block = '\n'
    for idx in indices:
        entry = afp.entries[idx]
        authors_string = ', '.join(author.name for author in entry.authors)
        formatted_entry = ('- ["%s"]('+'\n'+'%s'+'\n'+'"%s"),'+'\n'+
                     '%s,'+'\n'+'arXiv: [%s](%s),'+'\n'+'%s/%s') % (entry.title, 
                                                                    entry.link, 
                                                                    entry.summary, 
                                                                    authors_string,
                                                                    entry.id.split('abs/')[-1].split('v')[0], 
                                                                    entry.link,
                                                                    entry.published_parsed.tm_mon, 
                                                                    entry.published_parsed.tm_year)
        formatted_block = formatted_block+formatted_entry+'\n\n'
        
    return formatted_block

def add_papers_to_file(new_papers, filename = 'papers.md'):
    "Add new publications to lists in file papers.md"

    import pandas as pd
    import codecs # important to handle non-standard characters and unicode encoding properly (damn French names!)

    sublists = ['Applying Machine Learning to Physics',
            'Physics-Inspired Ideas Applied to Machine Learning', 
            'Quantum Computation and Quantum Algorithms for Machine Learning']

    d = {'Sublist': sublists, 'New': new_papers}
    df = pd.DataFrame(data=d)

    filepath = '/Users/annagolubeva/Desktop/oldwebsite/physicsml.github.io/develop/content/pages/'
       
    # buffer the file    
    with codecs.open(filepath+filename, 'r', 'utf-8') as fh0:
        buf = fh0.readlines()
    
    # now re-write the file with lines added
    with codecs.open(filepath+filename, 'w', 'utf-8') as fh:
        idx = 0
        for line in buf:
            if line == ('## '+df.Sublist[idx]+'\n'):
                line = line + df.New[idx] + '\n'
                if idx<df.index[-1]:
                    idx = idx+1
            fh.write(line)
    fh.close()

def add_to_csv_list(afp, indices_selected, filename = 'papers_ids_titles_sublists.csv'):
    "Adds new papers to the csv file."
    
    import pandas as pd
    import codecs # important to handle non-standard characters and unicode encoding properly (damn French names!)

    filepath = '/Users/annagolubeva/Desktop/oldwebsite/physicsml.github.io/develop/content/pages/'

    if (filename=='papers_ids_titles_sublists.csv'):
        sublistn = len(indices_selected[0])*[0]+len(indices_selected[1])*[1]+len(indices_selected[2])*[2]
        indices_selected = [index for onelist in indices_selected for index in onelist]
    
    entries = [afp.entries[index] for index in indices_selected]
    idlist = [entry.id.split('abs/')[-1].split('v')[0] for entry in entries]
    titles = [entry.title for entry in entries]

    # get entries from file and add new
    df = pd.read_csv(filepath+filename)
    a = idlist+[elem for elem in df.ID]
    b = titles+[elem for elem in df.Title]
    
    if (filename=='papers_ids_titles_sublists.csv'):
        c = sublistn+[elem for elem in df.Sublist]
        d = {'ID': a, 'Title': b, 'Sublist': c}
    else:
        d = {'ID': a, 'Title': b}
    
    # update the file
    df = pd.DataFrame(data=d)
    df.index.name = 'Index'

    df.to_csv(filepath+filename, encoding='utf-8')
