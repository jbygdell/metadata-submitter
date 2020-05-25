"""Handle HTTP methods for server."""
from datetime import datetime
from typing import Dict, List, cast

from aiohttp import BodyPartReader, web
from aiohttp.web import Request, Response

from .parser import SubmissionXMLToJSONParser
from .translator import ActionToCRUDTranslator


class SiteHandler:
    """Backend HTTP method handler."""

    async def get_object(self, req: Request) -> Response:
        """Get one object by its accession id.

        :param req: Multi-part POST request
        :returns: JSON response containing metadata object
        """
        translator = ActionToCRUDTranslator({})
        accessionId = req.match_info['accessionId']
        schema = req.match_info['schema']
        object = translator.get_object_with_accessionId(schema, accessionId)
        return web.Response(body=object)

    async def submit_object(self, req: Request) -> Response:
        """Submit and save metadata object to database.

        This currently relies on the same method as submission.xml parsing.
        It would be probably better to have a separate
        method for parsing, since form submissions can be done asynchronously
        in frontend.

        :param req: Multi-part POST request containing xml file to be saved
        :returns: JSON response containing accessionId for submitted file
        """
        submissions = await self.extract_submissions(req)
        translator = ActionToCRUDTranslator(submissions)

        for schema, filenames in submissions.items():
            for filename in filenames.keys():
                accessionId = translator.add({"schema": schema,
                                              "source": filename})

        return web.Response(body=accessionId)

    @staticmethod
    def generate_receipt(successful: List, unsuccessful: List) -> str:
        """Generate receipt XML after all submissions have ran through.

        Not currently valid receipt (against schema), will be changed later.

        :param successful: Succesful submissions and their info
        :param unsuccessful: Unuccesful submissions and their info
        :returns: XML-based receipt
        """
        date = datetime.now()
        infos = "<SUBMISSION accession=\"ERA521986\" alias=\"submission_1\" />"
        receipt = (f"<RECEIPT receiptDate = \"{date}\" success = \"true\" >"
                   f"{infos}"
                   f"</RECEIPT>")
        return receipt

    async def submit(self, req: Request) -> Response:
        """Handle submission to server containing submission.xml file.

        Note: This handles only direct POST XML submissions, frontend uses
        REST api for submissions.

        First submission info is parsed and then for every action in submission
        (such as "add", or "modify") corresponding operation is performed.
        Finally submission info itself is added.

        :param req: Multipart POST request with submission.xml and files
        :raises: HTTP Exceptions with status code 201 or 400
        :returns: XML-based receipt from submission
        """
        submissions = await self.extract_submissions(req)

        if "submission" not in submissions:
            reason = "There must be a submission.xml file in submission."
            raise web.HTTPBadRequest(reason=reason)

        if len(submissions["submission"]) > 1:
            reason = "You should submit only one submission.xml file."
            raise web.HTTPBadRequest(reason=reason)

        parser = SubmissionXMLToJSONParser()
        translator = ActionToCRUDTranslator(submissions)
        submission_xml = list(submissions["submission"].values())[0]
        submission_json = parser.parse("submission", submission_xml)

        successful: List = []
        unsuccessful: List = []

        for action_info in submission_json["action_infos"]:
            try:
                action = action_info["action"]
                if getattr(translator, action)(action_info):
                    successful.append(action)
                else:
                    unsuccessful.append(action)
                    break
            except AttributeError as error:
                reason = (f"Unfortunately this feature has not yet been "
                          f"implemented. More info: {error}")
                raise web.HTTPBadRequest(reason=reason)

        # translator.add({"schema": "submission"})
        receipt = self.generate_receipt(successful, unsuccessful)

        return web.Response(body=receipt, status=201, content_type="text/xml")

    @staticmethod
    async def extract_submissions(req: Request) -> Dict[str, Dict[str, str]]:
        """Extract submitted xml-files from multi-part request.

        :param req: Multi-part POST request
        :returns: Filename and content for each submitted xml, grouped by
        schemas
        """
        # Schemas are used also in action sorting, so they probably should be
        # used via class later. Refactor this in the future:
        ok_types = {"submission", "study", "sample", "experiment", "run",
                    "analysis", "dac", "policy", "dataset", "project"}
        submissions: Dict[str, Dict[str, str]] = {}
        reader = await req.multipart()
        while True:
            part = await reader.next()
            # Following is probably error in aiohttp type hints, fixing so
            # mypy doesn't complain about it. No runtime consequences.
            part = cast(BodyPartReader, part)
            if not part:
                break
            xml_type = part.name.lower()
            # Check if sent form contains correct information
            if xml_type not in ok_types:
                raise web.HTTPBadRequest(reason="Not ok type")
            if part.filename is None:
                raise web.HTTPBadRequest(reason="Filename should be included.")
            filename = part.filename
            data = []
            while True:
                chunk = await part.read_chunk()
                if not chunk:
                    break
                data.append(chunk)
            xml_content = ''.join(x.decode('UTF-8') for x in data)
            if xml_type not in submissions:
                submissions[xml_type] = {}
            submissions[xml_type][filename] = xml_content
        return submissions
