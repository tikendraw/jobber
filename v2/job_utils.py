import re


def extract_job_id(url:str)->str:
  """
  Extracts the job ID from a LinkedIn job URL.

  Args:
      url: The LinkedIn job URL.

  Returns:
      The extracted job ID as a string, or None if not found.
  """

  # Check for common patterns:
  # 1. /jobs/view/_id_here_/
  if "jobs/view/" in url:
    parts = url.split("/")
    for part in parts:
      if part.isdigit():
        return part

  # 2. ?currentJobId=_id_here_&
  if "?" in url:
    query_params = url.split("?")[-1].split("&")
    for param in query_params:
      if "currentJobId=" in param:
        return param.split("=")[1]

  # If no match, return None
  return None




if __name__=='__main__':
    job_urls={
        "4086596779":"https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4086596779",
        "4086596778":"https://www.linkedin.com/jobs/view/4086596778",
        "4090836133":"https://www.linkedin.com/jobs/collections/similar-jobs/?currentJobId=4090836133&originToLandingJobPostings=4090836133&referenceJobId=4086596779"
        
    }
    for i,j in job_urls.items():
        assert extract_job_id(j)==i
