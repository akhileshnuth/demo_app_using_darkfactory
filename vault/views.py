
# Add Import for required Libraries
import csv
import zipfile
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage

# Add the ExportView class
class ExportView(LoginRequiredMixin, View):
    def get(self, request):
        user_documents = Document.objects.filter(owner=request.user)

        # Create a zip file in memory
        zip_filename = 'vault_data.zip'
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={zip_filename}'

        with zipfile.ZipFile(response, 'w') as zip_file:
            # Prepare data for CSV
            csv_file_path = 'vault_data_summary.csv'
            csv_file = StringIO()
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Title', 'Type', 'Category', 'Issue Date', 'Expiry Date', 'Notes'])

            for document in user_documents:
                # Save document file to zip
                document_file_path = document.file.name
                zip_file.write(document_file_path, document_file.name)
                # Add a row to the CSV
                csv_writer.writerow([
                    document.title,
                    document.document_type,
                    document.category,
                    document.issue_date,
                    document.expiry_date,
                    document.notes,
                ])

            # Save the CSV to the zip
            zip_file.writestr(csv_file_path, csv_file.getvalue())
        return response
