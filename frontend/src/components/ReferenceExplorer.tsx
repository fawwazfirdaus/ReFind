import React, { useState, useEffect } from 'react';
import { searchReferences, getQueueStatus, getReferenceContent } from '../utils/api';
import { Paper, TextField, Button, Card, CardContent, Typography, CircularProgress, Chip, Box, Grid } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ArticleIcon from '@mui/icons-material/Article';
import PeopleIcon from '@mui/icons-material/People';

interface Reference {
  ref_id: string;
  title: string;
  authors: Array<{
    firstname: string;
    lastname: string;
    affiliation?: string;
  }>;
  matches: Array<{
    text: string;
    chunk_index: number;
    start_line: number;
    end_line: number;
  }>;
}

interface QueueStatus {
  queue_size: number;
  processed_count: number;
  is_processing: boolean;
}

interface ReferenceContent {
  metadata: {
    title: string;
    abstract?: string;
    authors: Array<{
      firstname: string;
      lastname: string;
      affiliation?: string;
    }>;
  };
  chunks: Array<{
    text: string;
    metadata: {
      chunk_index: number;
      start_line: number;
      end_line: number;
      ref_id: string;
    };
  }>;
}

export default function ReferenceExplorer() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Reference[]>([]);
  const [selectedReference, setSelectedReference] = useState<string | null>(null);
  const [referenceContent, setReferenceContent] = useState<ReferenceContent | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch queue status periodically
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await getQueueStatus();
        setQueueStatus(status);
      } catch (error) {
        console.error('Error fetching queue status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsLoading(true);
    try {
      const results = await searchReferences(searchQuery);
      setSearchResults(results);
    } catch (error) {
      console.error('Error searching references:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReferenceClick = async (refId: string) => {
    try {
      const content = await getReferenceContent(refId);
      setSelectedReference(refId);
      setReferenceContent(content);
    } catch (error) {
      console.error('Error fetching reference content:', error);
    }
  };

  return (
    <div className="p-4">
      {/* Search Section */}
      <Paper className="p-4 mb-4">
        <Typography variant="h5" className="mb-4">
          Reference Explorer
        </Typography>
        
        {/* Queue Status */}
        {queueStatus && (
          <Box className="mb-4">
            <Typography variant="subtitle2" color="textSecondary">
              Processing Status:
            </Typography>
            <Box display="flex" gap={2}>
              <Chip
                label={`Queue: ${queueStatus.queue_size}`}
                color={queueStatus.queue_size > 0 ? 'warning' : 'success'}
              />
              <Chip
                label={`Processed: ${queueStatus.processed_count}`}
                color="primary"
              />
              {queueStatus.is_processing && (
                <Chip
                  label="Processing..."
                  icon={<CircularProgress size={16} />}
                  color="info"
                />
              )}
            </Box>
          </Box>
        )}
        
        {/* Search Input */}
        <Box display="flex" gap={2}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search across referenced papers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
            disabled={isLoading}
          >
            Search
          </Button>
        </Box>
      </Paper>

      {/* Results Section */}
      <Grid container spacing={3}>
        {/* Search Results */}
        <Grid item xs={12} md={selectedReference ? 6 : 12}>
          {isLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            searchResults.map((ref) => (
              <Card
                key={ref.ref_id}
                className={`mb-4 ${selectedReference === ref.ref_id ? 'border-primary' : ''}`}
                onClick={() => handleReferenceClick(ref.ref_id)}
                sx={{ cursor: 'pointer' }}
              >
                <CardContent>
                  <Typography variant="h6" className="mb-2">
                    <ArticleIcon className="mr-2" />
                    {ref.title}
                  </Typography>
                  
                  <Box display="flex" alignItems="center" className="mb-2">
                    <PeopleIcon className="mr-2" />
                    <Typography variant="body2" color="textSecondary">
                      {ref.authors.map(a => `${a.firstname} ${a.lastname}`).join(', ')}
                    </Typography>
                  </Box>
                  
                  {ref.matches.map((match, idx) => (
                    <Card key={idx} variant="outlined" className="mt-2 p-2">
                      <Typography variant="body2">
                        {match.text}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Lines {match.start_line}-{match.end_line}
                      </Typography>
                    </Card>
                  ))}
                </CardContent>
              </Card>
            ))
          )}
        </Grid>

        {/* Reference Content */}
        {selectedReference && (
          <Grid item xs={12} md={6}>
            <Paper className="p-4">
              {referenceContent ? (
                <>
                  <Typography variant="h6" className="mb-4">
                    {referenceContent.metadata.title}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="textSecondary" className="mb-2">
                    Abstract
                  </Typography>
                  <Typography variant="body2" className="mb-4">
                    {referenceContent.metadata.abstract}
                  </Typography>
                  
                  <Typography variant="subtitle2" color="textSecondary" className="mb-2">
                    Content Sections
                  </Typography>
                  {referenceContent.chunks.map((chunk, idx) => (
                    <Card key={idx} variant="outlined" className="mb-2 p-2">
                      <Typography variant="body2">
                        {chunk.text}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Chunk {chunk.metadata.chunk_index}
                      </Typography>
                    </Card>
                  ))}
                </>
              ) : (
                <CircularProgress />
              )}
            </Paper>
          </Grid>
        )}
      </Grid>
    </div>
  );
} 