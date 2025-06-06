import logging
from typing import Dict, List, Any, Optional
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .config import TARGET_NAMES, LANGS, COLUMN_INFO, CHECK_RESULTS, FINAL_CHECK_RESULTS, COLUMNS
from .sheet_structure import SheetStructure, CheckInfo
from .cell_data import CellData, CellType
from .condition_formatter import ConditionFormatter
from .sheet_formatter import SheetFormatter
from .data_processor import DataProcessor
from .utils import create_version_info_request, adjust_sheet_size

logger = logging.getLogger(__name__)

class ChecklistSheetGenerator:
    """Generates Google Sheets checklists from source data"""
    
    def __init__(self, credentials: Credentials, spreadsheet_id: str, editor_email: str = ""):
        """Initialize the generator
        
        Args:
            credentials: Google API credentials
            spreadsheet_id: Target spreadsheet ID
            editor_email: Email address of editor for protected ranges
        """
        self.service = build('sheets', 'v4', credentials=credentials)
        self.spreadsheet_id = spreadsheet_id
        self.editor_email = editor_email
        self.sheets: Dict[str, SheetStructure] = {}
        self.existing_sheets: Dict[str, Dict[str, Any]] = {}
        self.current_lang: str = 'ja'
        self.current_target: str = ''
        self.data_processor = DataProcessor()
        self._load_existing_sheets()

    def _load_existing_sheets(self) -> None:
        """Load existing sheet information including protected ranges from spreadsheet"""
        try:
            # スプレッドシートの基本情報を取得
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            logger.debug("Loading existing sheets")            
            self.existing_sheets = {}
            self.protected_ranges = {}  # 保護範囲情報を格納する辞書
            
            for sheet in spreadsheet.get('sheets', []):
                properties = sheet['properties']
                title = properties['title']
                sheet_id = properties['sheetId']
                logger.debug(f"Found existing sheet: '{title}'")
                self.existing_sheets[title] = {
                    'sheetId': sheet_id,
                    'index': properties.get('index', 0)
                }
                
                # 保護範囲情報があれば取得
                if 'protectedRanges' in sheet:
                    self.protected_ranges[sheet_id] = [
                        protected_range.get('protectedRangeId')
                        for protected_range in sheet.get('protectedRanges', [])
                        if 'protectedRangeId' in protected_range
                    ]
                    if self.protected_ranges[sheet_id]:
                        logger.debug(f"Found {len(self.protected_ranges[sheet_id])} protected ranges in sheet '{title}'")
            
            logger.debug(f"Loaded existing sheets: {list(self.existing_sheets.keys())}")
            
            # 保護範囲の詳細情報を取得
            if any(self.protected_ranges.values()):
                try:
                    # 保護範囲の詳細情報を取得するには別のAPI呼び出しが必要
                    protected_ranges_response = self.service.spreadsheets().getByDataFilter(
                        spreadsheetId=self.spreadsheet_id,
                        body={
                            "dataFilters": [
                                {"developerMetadataLookup": {"metadataKey": "protectedRanges"}}
                            ]
                        }
                    ).execute()
                    
                    # 追加の処理が必要であれば、ここに書く
                    # 必要に応じて protected_ranges_response からさらに詳細情報を抽出
                    
                except Exception as e:
                    # 詳細情報の取得に失敗してもプログラムを続行する
                    logger.warning(f"Failed to get detailed protected ranges info: {e}")
        except Exception as e:
            logger.error(f"Error loading existing sheets: {e}")
            raise

    def initialize_spreadsheet(self) -> None:
        """Initialize spreadsheet by removing extra sheets"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            # Delete sheets after first
            if len(spreadsheet.get('sheets', [])) > 1:
                delete_requests = [
                    {'deleteSheet': {'sheetId': sheet['properties']['sheetId']}}
                    for sheet in spreadsheet['sheets'][1:]
                ]
                
                if delete_requests:
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body={'requests': delete_requests}
                    ).execute()
                    logger.info("Deleted existing sheets except the first one")
            
            # Reset existing sheets info
            self.existing_sheets = {
                spreadsheet['sheets'][0]['properties']['title']: {
                    'sheetId': spreadsheet['sheets'][0]['properties']['sheetId'],
                    'index': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error initializing spreadsheet: {e}")
            raise

    def prepare_sheet_structure(
        self,
        target_id: str,
        target_name: str,
        lang: str,
        checks: List[Dict]
    ) -> SheetStructure:
        """Prepare sheet structure for target
        
        Args:
            target_id: Target identifier
            target_name: Display name of target
            lang: Language code
            checks: List of checks for this target
            
        Returns:
            SheetStructure: Prepared sheet structure
        """
        self.current_lang = lang
        self.current_target = target_id
        
        logger.info(f"Preparing sheet structure: target_id={target_id}, target_name={target_name}, lang={lang}")
        sheet = SheetStructure(name=target_name, sheet_id=None)
        
        # Prepare headers
        headers = self.get_header_names(target_id, lang)
        header_row = []
        for header in headers:
            header_row.append(CellData(
                value=header,
                type=CellType.PLAIN,
                formatting={"textFormat": {"bold": True}}
            ))
        sheet.data.append(header_row)
        
        # Map IDs to rows
        id_to_row = self._create_id_row_mapping(checks)
        
        # Prepare data rows
        for check in checks:
            row_data = self.prepare_row_data(check, target_id, lang, id_to_row)
            sheet.data.append(row_data)
        
        # Add conditional formatting
        data_length = len(sheet.data)
        formatter = SheetFormatter(self.current_lang, self.current_target, self.editor_email)
        sheet.conditional_formats.extend(formatter.add_conditional_formatting(sheet.sheet_id, data_length))
        
        return sheet

    def get_header_ids(self, target_id: str) -> List[str]:
        """Get column IDs for sheet
        
        Args:
            target_id: Target identifier
            
        Returns:
            List[str]: Column IDs
        """
        # Column groups in order
        id_headers = COLUMNS['idCols']
        generated_headers = COLUMNS[target_id]['generatedData']
        user_headers = COLUMNS['userEntered']
        plain_headers = [
            *COLUMNS['common']['plainData1'],
            *COLUMNS[target_id]['plainData1'],
            *COLUMNS['common']['plainData2'],
            *COLUMNS[target_id]['plainData2']
        ]
        link_headers = [
            *COLUMNS[target_id]['linkData'],
            *COLUMNS['common']['linkData']
        ]
        
        # All headers in order
        all_headers = [
            *id_headers,
            *generated_headers,
            *user_headers,
            *plain_headers,
            *link_headers
        ]

        return all_headers

    def get_header_names(self, target_id: str, lang: str) -> List[str]:
        """Get localized column header names for sheet
        
        Args:
            target_id: Target identifier
            lang: Language code
            
        Returns:
            List[str]: Localized header names
        """
        all_headers = self.get_header_ids(target_id)

        # Get localized names
        return [
            COLUMN_INFO['name'].get(header, {}).get(lang, header)
            for header in all_headers
        ]

    def prepare_row_data(
        self,
        check: Dict,
        target_id: str,
        lang: str,
        id_to_row: Dict[str, int]
    ) -> List[CellData]:
        """Prepare data for a single row
        
        Args:
            check: Check data to process
            target_id: Target identifier 
            lang: Language code
            id_to_row: Mapping of IDs to row numbers
            
        Returns:
            List[CellData]: List of prepared cell data
        """
        row_data = []
        
        # Add ID columns
        for header in COLUMNS['idCols']:
            row_data.append(CellData(
                value=check[header],
                type=CellType.PLAIN,
                formatting={'numberFormat': {'type': 'TEXT', 'pattern': '0000'}}
            ))
            
        # Add generated data if needed
        if COLUMNS[target_id]['generatedData']:
            self._add_generated_data(check, target_id, lang, row_data, id_to_row)
            
        # Add user entry columns
        self._add_user_entry_columns(check, target_id, lang, row_data)
        
        # Add plain data columns
        self._add_plain_data_columns(check, target_id, lang, row_data)
        
        # Add link columns
        self._add_link_columns(check, target_id, lang, row_data)
        
        return row_data

    def _add_generated_data(
        self,
        check: Dict,
        target_id: str,
        lang: str,
        row_data: List[CellData],
        id_to_row: Dict[str, int]
    ) -> None:
        """Add generated data columns to row
        
        Args:
            check: Check data
            target_id: Target identifier
            lang: Language code
            row_data: Row data to append to
            id_to_row: ID to row mapping
        """
        is_subcheck = check.get('isSubcheck', False)
        has_subchecks = (
            not is_subcheck and
            check.get('subchecks') and
            target_id in check['subchecks'] and
            check['subchecks'][target_id].get('count', 0) > 1
        )
        
        formatter = ConditionFormatter(CHECK_RESULTS, FINAL_CHECK_RESULTS, target_id)
        
        if check.get('conditions'):
            for condition in check['conditions']:
                if condition['target'] == target_id:
                    formula = formatter.get_condition_formula(condition, id_to_row, lang)
                    
                    if not is_subcheck:
                        # Parent check
                        # Calculate column for calculatedResult (second generatedData column)
                        calc_col = chr(ord('A') + len(COLUMNS['idCols']) + 1)  # +1 for finalResult
                        ref_col = f'{calc_col}{id_to_row[check["id"]]}'
                        row_data.extend([
                            CellData(
                                value=f'=IF({ref_col}="","{CHECK_RESULTS["unchecked"][lang]}",{ref_col})',
                                type=CellType.FORMULA,
                                protection=True
                            ),
                            CellData(
                                value=formula,
                                type=CellType.FORMULA,
                                protection=True
                            )
                        ])
                    else:
                        # Subcheck
                        parent_id = check['id'].split('-')[0]
                        parent_row = id_to_row[parent_id]
                        row_data.extend([
                            CellData(value="", type=CellType.PLAIN, protection=True),
                            CellData(
                                value=f'={calc_col}{parent_row}',
                                type=CellType.FORMULA,
                                protection=True
                            )
                        ])
                    return
                    
        # Simple check case
        if not is_subcheck:
            # Calculate column positions
            calc_col = chr(ord('A') + len(COLUMNS['idCols']) + 1)  # +1 for finalResult
            result_col = chr(ord('A') + len(COLUMNS['idCols']) + len(COLUMNS[target_id]['generatedData']))
            result_cell = f'{result_col}{id_to_row[check["id"]]}'
            calc_cell = f'{calc_col}{id_to_row[check["id"]]}'
            row_data.extend([
                CellData(
                    value=f'=IF(${calc_cell}="","{CHECK_RESULTS["unchecked"][lang]}",${calc_cell})',
                    type=CellType.FORMULA,
                    protection=True
                ),
                CellData(
                    value=(
                        f'=IF(${result_cell}="{CHECK_RESULTS["unchecked"][lang]}", "", '
                        f'IF(TO_TEXT(${result_cell})="{CHECK_RESULTS["pass"][lang]}", '
                        f'"{FINAL_CHECK_RESULTS["pass"][lang]}", "{FINAL_CHECK_RESULTS["fail"][lang]}"))'
                    ),
                    type=CellType.FORMULA,
                    protection=True
                )
            ])
        else:
            # Calculate column for calculatedResult
            calc_col = chr(ord('A') + len(COLUMNS['idCols']) + 1)  # +1 for finalResult
            parent_id = check['id'].split('-')[0]
            parent_row = id_to_row[parent_id]
            row_data.extend([
                CellData(value="", type=CellType.PLAIN, protection=True),
                CellData(
                    value=f'={calc_col}{parent_row}',
                    type=CellType.FORMULA,
                    protection=True
                )
            ])

    def _add_user_entry_columns(
        self,
        check: Dict,
        target_id: str,
        lang: str,
        row_data: List[CellData]
    ) -> None:
        """Add user entry columns to row
        
        Args:
            check: Check data
            target_id: Target identifier
            lang: Language code
            row_data: Row data to append to
        """
        validation_dict = CHECK_RESULTS if COLUMNS[target_id]['generatedData'] else FINAL_CHECK_RESULTS
        validation_values = [validation_dict[key][lang] for key in validation_dict.keys()]
        validation_rule = {
            'condition': {
                'type': 'ONE_OF_LIST',
                'values': [{'userEnteredValue': val} for val in validation_values]
            },
            'strict': True,
            'showCustomUi': True
        }
        
        is_subcheck = check.get('isSubcheck', False)
        has_subchecks = (
            not is_subcheck and
            check.get('subchecks') and
            target_id in check['subchecks'] and
            check['subchecks'][target_id].get('count', 0) > 1
        )
        
        for header in COLUMNS['userEntered']:
            if header == 'result':
                if has_subchecks:
                    row_data.append(CellData(
                        value="",
                        type=CellType.PLAIN,
                        protection=True,
                        formatting={'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}}
                    ))
                else:
                    row_data.append(CellData(
                        value=validation_dict['unchecked'][lang],
                        type=CellType.PLAIN,
                        validation=validation_rule
                    ))
            else:
                row_data.append(CellData(value='', type=CellType.PLAIN))

    def _add_plain_data_columns(
        self,
        check: Dict,
        target_id: str,
        lang: str,
        row_data: List[CellData]
    ) -> None:
        """Add plain data columns to row
        
        Args:
            check: Check data
            target_id: Target identifier
            lang: Language code
            row_data: Row data to append to
        """
        from .utils import l10n_string
        
        plain_headers = [
            *COLUMNS['common']['plainData1'],
            *COLUMNS[target_id]['plainData1'],
            *COLUMNS['common']['plainData2'],
            *COLUMNS[target_id]['plainData2']
        ]
        
        for header in plain_headers:
            value = check.get(header, '')
            if isinstance(value, dict) and {'ja', 'en'}.intersection(value.keys()):
                value = l10n_string(value, lang)
            row_data.append(CellData(
                value=value or '',
                type=CellType.PLAIN
            ))

    def _add_link_columns(
        self,
        check: Dict,
        target_id: str,
        lang: str,
        row_data: List[CellData]
    ) -> None:
        """Add link columns to row
        
        Args:
            check: Check data
            target_id: Target identifier
            lang: Language code
            row_data: Row data to append to
        """
        link_headers = [
            *COLUMNS[target_id]['linkData'],
            *COLUMNS['common']['linkData']
        ]
        
        for header in link_headers:
            links = check.get(header, [])
            if links:
                row_data.append(self._create_rich_text_cell(links, lang))
            else:
                row_data.append(CellData(value='', type=CellType.PLAIN))

    def _create_rich_text_cell(self, links: List[Dict], lang: str) -> CellData:
        """Create rich text cell with formatted links
        
        Args:
            links: List of link data
            lang: Language code
            
        Returns:
            CellData: Formatted cell data
        """
        text_parts = []
        format_runs = []
        current_index = 0
        
        for i, link in enumerate(links):
            if i > 0:
                text_parts.append("\n")
                current_index += 1
                
            link_text = link['text'][lang]
            text_parts.append(link_text)
            
            url = link['url'][lang]
            # Check if URL is relative and needs base_url
            if url.startswith('/'):
                from freee_a11y_gl import settings as GL
                base_url = GL.get('base_url', '')
                url = base_url.rstrip('/') + url
            
            format_runs.append({
                'startIndex': current_index,
                'format': {
                    'link': {'uri': url},
                    'foregroundColor': {'red': 0.06, 'green': 0.47, 'blue': 0.82},
                    'underline': True
                }
            })
            current_index += len(link_text)
        
        return CellData(
            value={'text': ''.join(text_parts), 'format_runs': format_runs},
            type=CellType.RICH_TEXT
        )

    def _create_id_row_mapping(self, checks: List[Dict]) -> Dict[str, int]:
        """Create mapping of IDs to row numbers
        
        Args:
            checks: List of checks
            
        Returns:
            Dict[str, int]: Mapping of IDs to row numbers
        """
        id_to_row = {}
        current_row = 2  # Start after header
        
        for check in checks:
            if check.get('isSubcheck'):
                continue
                
            check_id = check['id']
            id_to_row[check_id] = current_row
            
            # Map procedure IDs
            if check.get('conditions'):
                for condition in check['conditions']:
                    if condition['target'] == self.current_target:
                        if condition['type'] == 'simple':
                            proc_id = condition['procedure']['id']
                            id_to_row[proc_id] = current_row
                        else:
                            self._map_procedure_ids(condition, id_to_row, current_row)

            # Map subcheck IDs
            subchecks = check.get('subchecks', {}).get(self.current_target, {})
            if subchecks and 'conditions' in subchecks:
                subcheck_count = len(subchecks['conditions'])
                
                for i, subcheck in enumerate(subchecks['conditions'], start=1):
                    subcheck_row = current_row + i
                    id_to_row[subcheck['id']] = subcheck_row
                    
                    if subcheck.get('conditions'):
                        for condition in subcheck['conditions']:
                            if condition['type'] == 'simple':
                                proc_id = condition['procedure']['id']
                                id_to_row[proc_id] = subcheck_row
                            else:
                                self._map_procedure_ids(condition, id_to_row, subcheck_row)
                
                current_row += subcheck_count
                
            current_row += 1

        return id_to_row

    def _map_procedure_ids(
        self,
        condition: Dict,
        id_to_row: Dict[str, int],
        row: int
    ) -> None:
        """Map procedure IDs to rows
        
        Args:
            condition: Condition to process
            id_to_row: ID to row mapping to update
            row: Current row number
        """
        if condition['type'] == 'simple':
            id_to_row[condition['procedure']['id']] = row
        else:
            for cond in condition['conditions']:
                self._map_procedure_ids(cond, id_to_row, row)

    def generate_checklist(self, source_data: Dict[str, Any], initialize: bool = False) -> None:
        """Generate complete checklist with progress reporting
        
        Args:
            source_data: Source data to process
            initialize: Whether to initialize spreadsheet first
        """
        if initialize:
            logger.info("Initializing spreadsheet (removing existing sheets)")
            self.initialize_spreadsheet()
            self._load_existing_sheets()

        # Store version info for later use
        self._version_info = {
            'version': source_data.get('version', ''),
            'date': source_data.get('date', '')
        }
        logger.info(f"Checklist version: {self._version_info['version']} ({self._version_info['date']})")

        # Process source data
        logger.info("Processing source data")
        processed_data = self.data_processor.process_source_data(source_data['checks'])
        
        # Count total sheets to be generated for progress reporting
        total_sheets = 0
        for target_id in processed_data:
            if target_id in TARGET_NAMES:
                total_sheets += len(LANGS)
        
        logger.info(f"Will generate {total_sheets} sheets ({len(processed_data)} targets × {len(LANGS)} languages)")

        # Generate sheets for each language and target
        sheets_processed = 0
        for lang in LANGS:
            for target_id, translations in TARGET_NAMES.items():
                if target_id in processed_data:
                    sheets_processed += 1
                    logger.info(f"Creating sheet {sheets_processed}/{total_sheets}: {target_id} in {lang} ({translations[lang]})")
                    
                    self.current_lang = lang
                    self.current_target = target_id
                    sheet = self.prepare_sheet_structure(
                        target_id=target_id,
                        target_name=translations[lang],
                        lang=lang,
                        checks=processed_data[target_id]
                    )
                    self.sheets[sheet.name] = sheet
        
        # Execute updates
        logger.info("All sheets prepared, executing batch update")
        self.execute_batch_update()
        logger.info("Checklist generation completed successfully")

    def execute_batch_update(self) -> None:
        """Execute batch update of spreadsheet with improved chunking for timeout prevention"""
        try:
            # Initial batch update
            initial_requests, pending_formats = self.generate_batch_requests()
            
            # Execute sheet creation requests
            creation_requests = [req for req in initial_requests if 'addSheet' in req]
            if creation_requests:
                logger.info(f"Creating sheets: {[req.get('addSheet', {}).get('properties', {}).get('title') for req in creation_requests]}")
                creation_response = self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': creation_requests}
                ).execute()
                
                # Update sheet IDs
                for reply in creation_response.get('replies', []):
                    if 'addSheet' in reply:
                        sheet_id = reply['addSheet']['properties']['sheetId']
                        sheet_title = reply['addSheet']['properties']['title']
                        self.existing_sheets[sheet_title] = {
                            'sheetId': sheet_id,
                            'index': 0
                        }

            # Generate and execute remaining updates
            update_requests, _ = self.generate_batch_requests()
            update_requests = [req for req in update_requests if 'addSheet' not in req]
            
            if update_requests:
                # Add version info request
                if hasattr(self, '_version_info'):
                    first_sheet_id = self.get_first_sheet_id()
                    version_update_request = create_version_info_request(
                        self._version_info['version'],
                        self._version_info['date'],
                        first_sheet_id
                    )
                    update_requests.append(version_update_request)
                
                # Process in smaller batches to avoid timeouts
                BATCH_SIZE = 50  # Reduced batch size to avoid timeout
                total_requests = len(update_requests)
                logger.info(f"Updating {total_requests} sheet contents in smaller batches")
                
                # タイムアウト回避のためのバッチ処理
                for i in range(0, total_requests, BATCH_SIZE):
                    end_idx = min(i + BATCH_SIZE, total_requests)
                    batch = update_requests[i:end_idx]
                    logger.info(f"Processing batch {i//BATCH_SIZE + 1}/{(total_requests-1)//BATCH_SIZE + 1}: requests {i+1}-{end_idx} of {total_requests}")
                    
                    try:
                        # タイムアウト設定を長めに
                        self.service.spreadsheets().batchUpdate(
                            spreadsheetId=self.spreadsheet_id,
                            body={'requests': batch}
                        ).execute()
                        logger.info(f"Batch {i//BATCH_SIZE + 1} completed successfully")
                    except Exception as e:
                        logger.error(f"Error in batch {i//BATCH_SIZE + 1}: {e}")
                        # エラーが発生しても次のバッチを続行
                
                logger.info(f"All sheet updates completed")
                                
        except Exception as e:
            logger.error(f"Error executing batch update: {e}")
            raise

    def generate_batch_requests(self) -> tuple[List[Dict], Dict]:
        """Generate batch update requests
        
        Returns:
            tuple[List[Dict], Dict]: Requests and pending formats
        """
        requests = []
        pending_formats = {}

        logger.info(f"Generating requests for sheets: {list(self.sheets.keys())}")

        for sheet_name, sheet in self.sheets.items():
            data_length = len(sheet.data)
            column_count = len(sheet.data[0]) if sheet.data else 26

            logger.debug(f"Processing sheet '{sheet_name}', exists: {sheet_name in self.existing_sheets}")

            # Get target ID and language
            target_id = None
            current_lang = None
            for tid, translations in TARGET_NAMES.items():
                for lang, name in translations.items():
                    if name == sheet_name:
                        target_id = tid
                        current_lang = lang
                        self.current_lang = lang
                        self.current_target = tid
                        break
                if target_id:
                    break

            if target_id is None:
                logger.warning(f"Could not find target_id for sheet: {sheet_name}")
                continue

            # Handle existing or new sheet
            if sheet_name in self.existing_sheets:
                sheet_id = self.existing_sheets[sheet_name]['sheetId']
                logger.debug(f"Updating existing sheet: {sheet_name} (id: {sheet_id})")
                
                formatter = SheetFormatter(current_lang, target_id, self.editor_email)

                # Add content and formatting
                self._add_sheet_content_requests(requests, sheet_id, sheet)
                requests.extend(formatter.apply_basic_formatting(sheet_id, data_length))
                requests.extend(formatter.add_conditional_formatting(sheet_id, data_length))
            else:
                # Create new sheet
                logger.info(f"Creating new sheet: {sheet_name} with {column_count} columns")
                requests.append({
                    'addSheet': {
                        'properties': {
                            'title': sheet_name,
                            'gridProperties': {
                                'rowCount': max(data_length + 1, 1000),
                                'columnCount': max(column_count, 26)
                            }
                        }
                    }
                })
                
                pending_formats[sheet_name] = {
                    'data_length': data_length,
                    'formats': []
                }

        return requests, pending_formats

    def _add_sheet_content_requests(
        self,
        requests: List[Dict],
        sheet_id: int,
        sheet: SheetStructure
    ) -> None:
        """Add requests to update sheet content and formatting
        
        Args:
            requests: List to append requests to
            sheet_id: ID of sheet to update
            sheet: Sheet structure containing data and format info
        """
        try:
            data_length = len(sheet.data)
            column_count = len(sheet.data[0]) if sheet.data else 26

            # Get current sheet properties and adjust size if needed
            self._adjust_sheet_size(sheet_id, sheet.name, data_length, column_count)
            
            # Clear existing content
            self._add_clear_content_request(requests, sheet_id, data_length, column_count)
            
            # Add new data in chunks
            self._add_data_update_requests(requests, sheet_id, sheet.data)
            
            # Set column widths
            self._add_column_width_requests(requests, sheet_id)
            
            # Add formatting and protection
            self._add_formatting_requests(requests, sheet_id, sheet, data_length)
            
            # Configure column visibility
            self._add_column_visibility_requests(requests, sheet_id, sheet.data, column_count)

        except Exception as e:
            logger.error(f"Error processing sheet content: {e}")
            raise

    def _adjust_sheet_size(self, sheet_id: int, sheet_name: str, data_length: int, column_count: int) -> None:
        """Adjust sheet size if needed"""
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id,
            ranges=[sheet_name],
            includeGridData=False
        ).execute()
        
        grid_properties = None
        for s in spreadsheet['sheets']:
            if s['properties']['title'] == sheet_name:
                grid_properties = s['properties']['gridProperties']
                break
                
        if grid_properties:
            current_rows = grid_properties.get('rowCount', 1000)
            current_cols = grid_properties.get('columnCount', 26)
            
            size_requests = adjust_sheet_size(
                sheet_id, data_length, column_count, 
                current_rows, current_cols
            )
            
            if size_requests:
                logger.debug("Executing size adjustment requests")
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': size_requests}
                ).execute()

    def _add_clear_content_request(
        self,
        requests: List[Dict],
        sheet_id: int,
        data_length: int,
        column_count: int
    ) -> None:
        """Add request to clear existing content and remove protected ranges
        
        Args:
            requests: List to append requests to
            sheet_id: ID of sheet to update
            data_length: Number of data rows
            column_count: Number of columns
        """
        # 既存の保護範囲を削除するリクエストを追加
        if hasattr(self, 'protected_ranges') and sheet_id in self.protected_ranges:
            for protected_range_id in self.protected_ranges.get(sheet_id, []):
                requests.append({
                    'deleteProtectedRange': {
                        'protectedRangeId': protected_range_id
                    }
                })
            logger.debug(f"Added requests to delete {len(self.protected_ranges.get(sheet_id, []))} protected ranges from sheet {sheet_id}")
        
        # 既存のセル内容をクリアするリクエスト
        requests.append({
            'updateCells': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': data_length,
                    'startColumnIndex': 0,
                    'endColumnIndex': column_count
                },
                'fields': '*'
            }
        })

    def _add_data_update_requests(
        self,
        requests: List[Dict],
        sheet_id: int,
        data: List[List[CellData]]
    ) -> None:
        """Add requests to update sheet data in chunks with improved batching
        
        Args:
            requests: List to append requests to
            sheet_id: ID of sheet to update
            data: Data to update
        """
        # Use smaller chunks for better reliability
        CHUNK_SIZE = 100  # Reduced from 1000 to avoid timeouts
        
        total_rows = len(data)
        logger.debug(f"Adding data update requests for {total_rows} rows in chunks of {CHUNK_SIZE}")
        
        for i in range(0, total_rows, CHUNK_SIZE):
            chunk = data[i:i + CHUNK_SIZE]
            end_idx = min(i + CHUNK_SIZE, total_rows)
            logger.debug(f"Processing rows {i+1}-{end_idx} of {total_rows}")
            
            requests.append({
                'updateCells': {
                    'rows': [
                        {'values': [cell.to_sheets_value() for cell in row]}
                        for row in chunk
                    ],
                    'fields': 'userEnteredValue,userEnteredFormat,textFormatRuns,dataValidation',
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': i,
                        'startColumnIndex': 0
                    }
                }
            })

    def _add_column_width_requests(self, requests: List[Dict], sheet_id: int) -> None:
        """Add requests to set column widths"""
        for i, width in enumerate(self._get_column_widths()):
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': i,
                        'endIndex': i + 1
                    },
                    'properties': {'pixelSize': width},
                    'fields': 'pixelSize'
                }
            })

    def _add_formatting_requests(
        self,
        requests: List[Dict],
        sheet_id: int,
        sheet: SheetStructure,
        data_length: int
    ) -> None:
        """Add formatting and protection requests"""
        formatter = SheetFormatter(self.current_lang, self.current_target, self.editor_email)
        
        # Basic formatting
        requests.extend(formatter.apply_basic_formatting(sheet_id, data_length))
        
        # Protection settings
        requests.extend(formatter.add_protection_settings(sheet_id, sheet))
        
        # Parent check protection
        for i, row in enumerate(sheet.data[1:], start=1):
            if self._is_parent_check_with_subchecks(row):
                requests.append(formatter.protect_parent_check_cells(sheet_id, i))

    def _add_column_visibility_requests(
        self,
        requests: List[Dict],
        sheet_id: int,
        data: List[List[CellData]],
        column_count: int
    ) -> None:
        """Add requests to configure column visibility"""
        # Reset all column visibility
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': column_count
                },
                'properties': {'hiddenByUser': False},
                'fields': 'hiddenByUser'
            }
        })
        
        has_generated_data = bool(COLUMNS[self.current_target]['generatedData'])
        has_subchecks = any(row[1].value for row in data[1:])  # Check B column after header
        
        if has_generated_data:
            if not has_subchecks:
                # Hide columns B-D if no subchecks
                requests.append({
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 1,
                            'endIndex': 4
                        },
                        'properties': {'hiddenByUser': True},
                        'fields': 'hiddenByUser'
                    }
                })
            else:
                # Hide column C and merge A-B for subchecks
                requests.append({
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 2,
                            'endIndex': 3
                        },
                        'properties': {'hiddenByUser': True},
                        'fields': 'hiddenByUser'
                    }
                })
                
                requests.append({
                    'mergeCells': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': 2
                        },
                        'mergeType': 'MERGE_ALL'
                    }
                })
        else:
            # Hide column B if no generated data
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 1,
                        'endIndex': 2
                    },
                    'properties': {'hiddenByUser': True},
                    'fields': 'hiddenByUser'
                }
            })

    def _is_parent_check_with_subchecks(self, row: List[CellData]) -> bool:
        """Check if the row represents a parent check that has subchecks
        
        Args:
            row: Row data
            
        Returns:
            bool: True if this is a parent check with subchecks
        """
        # checkIdを取得
        check_id = row[0].value if row[0].value else ""
        
        # チェック情報から判定
        if check_id in self.data_processor.check_info:
            check_info = self.data_processor.check_info[check_id]
            if check_info.is_subcheck:
                return False
                
            # 指定されたターゲットに対するサブチェック数を確認
            subcheck_count = check_info.subchecks_by_target.get(self.current_target, 0)
            return subcheck_count > 1
        
        return False

    def _get_column_widths(self) -> List[int]:
        """Get list of column widths
        
        Returns:
            List[int]: List of column widths
        """
        headers = self.get_header_ids(self.current_target)
        return [
            COLUMN_INFO['width'].get(header, 100)
            for header in headers
        ]

    def get_first_sheet_id(self) -> int:
        """Get ID of first sheet
        
        Returns:
            int: Sheet ID
            
        Raises:
            KeyError: If no sheets exist
        """
        first_sheet_name = next(iter(self.existing_sheets))
        return self.existing_sheets[first_sheet_name]['sheetId']
