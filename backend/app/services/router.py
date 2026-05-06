import asyncio
from typing import Dict, List
from fastapi import UploadFile

from app.services.link_inspector import LinkInspector
from app.services.document_parser import DocumentParser
from app.services.vision_engine import VisionEngine
import os


class AssetRouter:
    """
    Central router that coordinates parallel processing of all asset types.
    Implements the Perception layer of the Guardian LPU pipeline.
    """

    def __init__(self):
        self.link_inspector = LinkInspector()
        self.document_parser = DocumentParser()
        self.vision_engine = VisionEngine(api_key=os.getenv("GROQ_API_KEY"))

    async def initialize(self):
        """Initialize all services."""
        await self.link_inspector.initialize()

    async def cleanup(self):
        """Cleanup all services."""
        await self.link_inspector.cleanup()

    async def process_assets(self, urls: List[str], files: List[UploadFile]) -> Dict:
        """
        Process all assets in parallel:
        - URLs: scraped via LinkInspector
        - Files: parsed via DocumentParser
        - Screenshots: analyzed via VisionEngine
        """
        await self.initialize()

        # Read all files first
        file_contents = []
        for file in files:
            if file.filename:
                content = await file.read()
                file_contents.append({
                    'filename': file.filename,
                    'content': content,
                    'content_type': file.content_type or 'application/octet-stream'
                })

        # Create processing tasks
        tasks = []

        # URL inspection tasks
        if urls:
            url_tasks = [self.link_inspector.inspect_url(url) for url in urls]
            tasks.append(('urls', asyncio.gather(*url_tasks, return_exceptions=True)))

        # File parsing tasks
        if file_contents:
            file_tasks = [
                self.document_parser.parse_file(
                    f['filename'], f['content'], f['content_type']
                )
                for f in file_contents
            ]
            tasks.append(('documents', asyncio.gather(*file_tasks, return_exceptions=True)))

        # Execute all tasks and collect results
        results = {'urls': [], 'documents': []}

        for asset_type, task_group in tasks:
            try:
                completed = await task_group
                for result in completed:
                    if isinstance(result, Exception):
                        results[asset_type].append({'error': str(result)})
                    else:
                        results[asset_type].append(result)
            except Exception as e:
                results[asset_type].append({'error': str(e)})

        # Run vision analysis on any screenshots
        screenshots = []

        # Collect screenshots from link inspection
        for url_data in results['urls']:
            if 'screenshot' in url_data:
                screenshots.append({
                    'data': url_data['screenshot'],
                    'url': url_data.get('final_url', url_data.get('url')),
                    'source': 'webpage'
                })

        # Collect images from documents
        for doc in results['documents']:
            if 'images' in doc:
                for img in doc['images']:
                    if 'data' in img:
                        screenshots.append({
                            'data': img['data'].split(',')[1] if ',' in img['data'] else img['data'],
                            'url': doc.get('filename', 'document'),
                            'source': 'document'
                        })

        # Run vision analysis if we have screenshots
        if screenshots:
            vision_results = await self.vision_engine.batch_analyze(screenshots)

            # Attach vision results to URL data
            for i, url_data in enumerate(results['urls']):
                if i < len(vision_results):
                    url_data['vision_analysis'] = vision_results[i]

        return results
