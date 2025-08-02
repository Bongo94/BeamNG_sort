import zipfile
import json
import os
from typing import Optional, List, Dict
from core.mod_info import ModInfo, ModType
from utils.logger import logger
import re

class ModAnalyzer:
    @staticmethod
    def analyze_zip(zip_path: str) -> ModInfo:
        logger.debug(f"Analyzing zip file: {zip_path}")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                file_list = zf.namelist()
                logger.debug(f"File list: {file_list}")

                vehicle_info = ModAnalyzer._check_vehicle_mod(zf, file_list)
                if vehicle_info:
                    logger.info(f"Detected vehicle mod: {vehicle_info.name}")
                    return vehicle_info

                map_info = ModAnalyzer._check_map_mod(zf, file_list)
                if map_info:
                    logger.info(f"Detected map mod: {map_info.name}")
                    return map_info

                other_info = ModAnalyzer._create_other_mod_info(zf, file_list)
                logger.info(f"Detected other mod: {other_info.name}")
                return other_info
        except zipfile.BadZipFile as e:
            logger.error(f"Invalid zip file: {zip_path} - {e}")
            return ModAnalyzer._create_fallback_mod_info(zipfile.ZipFile(zip_path, 'r'), "", ModType.OTHER, f"Invalid zip file: {e}")
        except Exception as e:
            logger.exception(f"Error analyzing zip file: {zip_path}")
            return ModAnalyzer._create_fallback_mod_info(zipfile.ZipFile(zip_path, 'r'), "", ModType.OTHER, str(e))

    @staticmethod
    def _check_vehicle_mod(zf: zipfile.ZipFile, file_list: List[str]) -> Optional[ModInfo]:
        logger.debug(f"Checking for vehicle mod in {zf.filename}")
        info_file = next((name for name in file_list
                          if 'vehicles' in name.split('/') and 'info.json' in name), None)

        if not info_file:
            logger.debug("No vehicle info.json found.")
            return None

        logger.debug(f"Found vehicle info.json: {info_file}")

        try:
            with zf.open(info_file) as f:
                file_content = f.read().decode('utf-8', 'ignore')
            name = ModAnalyzer._extract_value_from_json_string(file_content, 'Name')
            author = ModAnalyzer._extract_value_from_json_string(file_content, 'Author')
            country = ModAnalyzer._extract_value_from_json_string(file_content, 'Country')
            derby_class = ModAnalyzer._extract_value_from_json_string(file_content, 'Derby Class')
            mod_type = ModAnalyzer._extract_value_from_json_string(file_content, 'Type')

            engine_type = ModAnalyzer._extract_value_from_json_string(file_content, 'Type', section='Engine')
            engine_configuration = ModAnalyzer._extract_value_from_json_string(file_content, 'Configuration', section='Engine')
            engine_displacement = ModAnalyzer._extract_value_from_json_string(file_content, 'Displacement', section='Engine')
            engine_power = ModAnalyzer._extract_value_from_json_string(file_content, 'Power', section='Engine')

            transmission_type = ModAnalyzer._extract_value_from_json_string(file_content, 'Type', section='Transmission')
            transmission_gears = ModAnalyzer._extract_value_from_json_string(file_content, 'Gears', section='Transmission')
            years_min = ModAnalyzer._extract_value_from_json_string(file_content, 'min', section='Years')
            years_max = ModAnalyzer._extract_value_from_json_string(file_content, 'max', section='Years')
            brand = ModAnalyzer._extract_value_from_json_string(file_content, 'Brand')
            body_style = ModAnalyzer._extract_value_from_json_string(file_content, 'Body Style')


        except Exception as e:
            logger.exception(f"Error in _check_vehicle_mod")
            return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.VEHICLE, str(e))

        preview_images = []
        base_dir = os.path.dirname(info_file)
        logger.debug(f"Base directory: {base_dir}")

        pc_files = [f for f in file_list if f.startswith(base_dir) and f.endswith('.pc')]
        logger.debug(f"PC files: {pc_files}")

        for pc_file in pc_files:
            config_name = os.path.splitext(os.path.basename(pc_file))[0]
            img_base = os.path.join(base_dir, config_name).replace('\\', '/')
            logger.debug(f"Image base: {img_base}")
            for ext in ['.png', '.jpg', '.jpeg']:
                img_path = img_base + ext
                if img_path in file_list:
                    try:
                        with zf.open(img_path) as img:
                            data = img.read()
                            logger.debug(f"Found image {img_path} with {len(data)} bytes")
                            preview_images.append((config_name, data))
                            break
                    except Exception as e:
                        logger.warning(f"Could not load image {img_path}: {e}")


        for default_name in ['default.png', 'default.jpg']:
            default_path = os.path.join(base_dir, default_name).replace('\\', '/')
            if default_path in file_list:
                try:
                    with zf.open(default_path) as img:
                        data = img.read()
                        logger.debug(f"Found default image {default_path} with {len(data)} bytes")
                        preview_images.insert(0, ('default', data))
                except Exception as e:
                    logger.warning(f"Could not load default image {default_path}: {e}")


        mod_info = ModInfo(
            name=name or 'Unknown',
            author=author or 'Unknown',
            type=ModType.VEHICLE,
            description=ModAnalyzer._format_vehicle_description_from_values(
                brand=brand,
                body_style=body_style,
                years_min=years_min,
                years_max=years_max,
                country=country,
                derby_class=derby_class,
                mod_type=mod_type,
                engine_type=engine_type,
                engine_configuration=engine_configuration,
                engine_displacement=engine_displacement,
                engine_power=engine_power,
                transmission_type=transmission_type,
                transmission_gears=transmission_gears
            ),
            preview_images=preview_images,
            additional_info={
                'country': country,
                'derby_class': derby_class,
                'type': mod_type,
                'configurations': [os.path.splitext(os.path.basename(pc))[0] for pc in pc_files],
                'raw_info': {'Name':name, 'Author': author, 'Country': country, 'Derby Class': derby_class, 'Type': mod_type}
            }
        )
        logger.info(f"Vehicle mod detected: {mod_info.name}".encode('utf-8').decode('ascii', errors='ignore'))
        return mod_info

    @staticmethod
    def _extract_value_from_json_string(json_string: str, key: str, section: str = None) -> Optional[str]:
        """
        Extracts a value from a JSON-like string using regular expressions.

        Args:
            json_string: The JSON-like string to extract from.
            key: The key to extract the value for.
            section: If the key is inside a nested section (e.g., "Engine"), specify the section name.

        Returns:
            The extracted value as a string, or None if not found.
        """
        try:
            if section:
                 pattern = re.compile(rf'"{section}"\s*:\s*{{.*??"{key}"\s*:\s*"([^"]*?)"', re.DOTALL | re.IGNORECASE)
            else:
                pattern = re.compile(rf'"{key}"\s*:\s*"([^"]*?)"', re.IGNORECASE)

            match = pattern.search(json_string)
            if match:
                return match.group(1)
            else:
                return None
        except Exception as e:
            logger.warning(f"Error extracting value for key '{key}' in section '{section}': {e}")
            return None


    @staticmethod
    def _format_vehicle_description_from_values(brand: str, body_style: str, years_min: str, years_max: str,
                                            country: str, derby_class: str, mod_type: str, engine_type: str,
                                            engine_configuration: str, engine_displacement: str, engine_power: str,
                                            transmission_type: str, transmission_gears: str) -> str:
        desc_parts = []

        def add_if_present(label: str, value: str):
            if value:
                desc_parts.append(f"{label}: {value}")
            else:
                desc_parts.append(f"{label}: N/A")

        add_if_present("Brand", brand)
        add_if_present("Body Style", body_style)
        add_if_present("Years", f"{years_min}-{years_max}" if years_min and years_max else years_min or years_max) # Handle single year
        add_if_present("Country", country)
        add_if_present("Derby Class", derby_class)
        add_if_present("Type", mod_type)

        engine_details = []
        def add_if_present_local(label, value):
             if value:
                engine_details.append(f"{label}: {value}")

        if engine_type or engine_configuration or engine_displacement or engine_power:  # Check if any engine detail is present
            desc_parts.append("\nEngine Details:")
            add_if_present_local("Type", engine_type)
            add_if_present_local("Configuration", engine_configuration)
            add_if_present_local("Displacement", engine_displacement)
            add_if_present_local("Power", engine_power)
            desc_parts.extend(engine_details)
            if not engine_details:
                desc_parts.append("N/A")


        trans_details = []
        def add_if_present_local(label, value):
             if value:
                trans_details.append(f"{label}: {value}")
        if transmission_type or transmission_gears:
            desc_parts.append("\nTransmission:")
            add_if_present_local("Type", transmission_type)
            add_if_present_local("Gears", transmission_gears)
            desc_parts.extend(trans_details)
            if not trans_details:
                desc_parts.append("N/A")


        return "\n".join(desc_parts)

    @staticmethod
    def _format_vehicle_description(info: Dict) -> str:
        logger.debug(f"Formatting vehicle description for: {info.get('Name', 'Unknown')}")
        desc_parts = [
            f"Brand: {info.get('Brand', 'N/A')}",
            f"Body Style: {info.get('Body Style', 'N/A')}",
            f"Years: {info.get('Years', {}).get('min', 'N/A')}-{info.get('Years', {}).get('max', 'N/A')}",
            f"Country: {info.get('Country', 'N/A')}",
            f"Derby Class: {info.get('Derby Class', 'N/A')}",
            f"Type: {info.get('Type', 'N/A')}"
        ]

        if 'Engine' in info:
            engine = info['Engine']
            logger.debug(f"Engine details: {engine}")
            desc_parts.extend([
                "\nEngine Details:",
                f"Type: {engine.get('Type', 'N/A')}",
                f"Configuration: {engine.get('Configuration', 'N/A')}",
                f"Displacement: {engine.get('Displacement', 'N/A')}",
                f"Power: {engine.get('Power', 'N/A')}"
            ])

        if 'Transmission' in info:
            trans = info['Transmission']
            logger.debug(f"Transmission details: {trans}")
            desc_parts.extend([
                "\nTransmission:",
                f"Type: {trans.get('Type', 'N/A')}",
                f"Gears: {trans.get('Gears', 'N/A')}"
            ])

        description = "\n".join(desc_parts)
        logger.debug(f"Formatted description: {description}")
        return description

    @staticmethod
    def _check_map_mod(zf: zipfile.ZipFile, file_list: List[str]) -> Optional[ModInfo]:
        """Check if zip contains map mod structure and extract info"""
        logger.debug(f"Checking for map mod in {zf.filename}")
        info_file = next((name for name in file_list
                          if 'levels' in name.split('/') and 'info.json' in name), None)

        if not info_file:
            logger.debug("No map info.json file found.")
            return None

        logger.debug(f"Found map info.json: {info_file}")

        try:
            with zf.open(info_file) as f:
                file_content = f.read().decode('utf-8', 'ignore')

            # Extract relevant info using regex
            title = ModAnalyzer._extract_value_from_json_string(file_content, 'title')
            authors = ModAnalyzer._extract_value_from_json_string(file_content, 'authors')
            biome = ModAnalyzer._extract_value_from_json_string(file_content, 'biome')
            description = ModAnalyzer._extract_value_from_json_string(file_content, 'description')
            roads_str = ModAnalyzer._extract_value_from_json_string(file_content, 'roads')
            suitablefor_str = ModAnalyzer._extract_value_from_json_string(file_content, 'suitablefor')

            roads = [s.strip() for s in roads_str.split(',')] if roads_str else []
            suitablefor = [s.strip() for s in suitablefor_str.split(',')] if suitablefor_str else []

            size_x = ModAnalyzer._extract_value_from_json_string(file_content, '0', section='size')
            size_y = ModAnalyzer._extract_value_from_json_string(file_content, '1', section='size')

            size_x = size_x if size_x else "N/A"
            size_y = size_y if size_y else "N/A"

            size = [size_x, size_y]
            previews_str = ModAnalyzer._extract_value_from_json_string(file_content, 'previews')

            previews = []
            if previews_str:
                previews = [s.strip().replace('"', '') for s in previews_str.strip('[]').split(',')]


        except Exception as e:
            logger.exception(f"Error in _check_map_mod")
            return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.MAP, str(e))

        preview_images = []
        base_dir = os.path.dirname(info_file)

        if previews:
            for preview in previews:
                preview_path = os.path.join(base_dir, preview)
                if preview_path in file_list:
                    try:
                        with zf.open(preview_path) as img:
                            preview_images.append((os.path.basename(preview), img.read()))
                            logger.debug(f"Found map preview image: {preview_path}")
                    except Exception as e:
                        logger.warning(f"Could not load preview image {preview_path}: {e}")

        mod_info = ModInfo(
            name=title or 'Unknown Map',
            author=authors or 'Unknown',
            type=ModType.MAP,
            description=ModAnalyzer._format_map_description_from_values(
                biome=biome,
                size=size,
                description=description,
                roads=roads,
                suitablefor=suitablefor
            ),
            preview_images=preview_images,
            additional_info={
                'roads': roads,
                'suitable_for': suitablefor,
                'spawn_points': [],
                'raw_info': {'title': title, 'authors': authors, 'biome': biome, 'description': description,
                             'roads': roads, 'suitablefor': suitablefor}
            }
        )

        logger.info(f"Map mod detected: {mod_info.name}".encode('utf-8').decode('ascii', errors='ignore'))
        return mod_info

    @staticmethod
    def _format_map_description_from_values(biome: str, size: List[str], description: str, roads: List[str],
                                            suitablefor: List[str]) -> str:
        """Formats the map description from extracted values."""
        desc_parts = []

        def add_if_present(label: str, value: str):
            if value:
                desc_parts.append(f"{label}: {value}")
            else:
                desc_parts.append(f"{label}: N/A")

        add_if_present("Biome", biome)
        add_if_present("Size", ' x '.join(size) if size else 'N/A')
        add_if_present("\nDescription", description)
        add_if_present("\nRoads", ', '.join(roads) if roads else 'N/A')
        add_if_present("Suitable for", ', '.join(suitablefor) if suitablefor else 'N/A')

        return "\n".join(desc_parts)

    @staticmethod
    def _format_map_description(info: Dict) -> str:
        logger.debug(f"Formatting map description for: {info.get('title', 'Unknown Map')}")
        desc_parts = [
            f"Biome: {info.get('biome', 'N/A')}",
            f"Size: {' x '.join(map(str, info.get('size', ['N/A', 'N/A'])))}",
            f"\nDescription: {info.get('description', 'N/A')}",
            f"\nRoads: {', '.join(info.get('roads', ['N/A']))}",
            f"Suitable for: {', '.join(info.get('suitablefor', ['N/A']))}"
        ]
        description = "\n".join(desc_parts)
        logger.debug(f"Formatted description: {description}")
        return description

    @staticmethod
    def _create_other_mod_info(zf: zipfile.ZipFile, file_list: List[str]) -> ModInfo:
        logger.debug(f"Creating 'other' mod info for: {zf.filename}")
        info_file = next((name for name in file_list if name.endswith('info.json')), None)
        info = {}

        if info_file:
            logger.debug(f"Found info.json: {info_file}")
            try:
                with zf.open(info_file) as f:
                    info = json.load(f)
                    logger.debug(f"Loaded info.json: {info}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSONDecodeError in _create_other_mod_info: {e}")
                return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.OTHER, str(e))
            except Exception as e:
                logger.exception(f"Error in _create_other_mod_info")
                return ModAnalyzer._create_fallback_mod_info(zf, info_file, ModType.OTHER, str(e))

        preview_images = []
        image_files = [f for f in file_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        logger.debug(f"Image files: {image_files}")
        for img_file in image_files[:3]:
            try:
                with zf.open(img_file) as img:
                    data = img.read()
                    logger.debug(f"Found image {img_file} with {len(data)} bytes")
                    preview_images.append((os.path.basename(img_file), data))
            except Exception as e:
                logger.warning(f"Could not load image {img_file}: {e}")


        mod_info = ModInfo(
            name=info.get('name', info.get('title', os.path.basename(zf.filename))),
            author=info.get('author', info.get('authors', 'Unknown')),
            type=ModType.OTHER,
            description="Unknown mod type. Please review contents manually.",
            preview_images=preview_images,
            additional_info=info
        )

        logger.info(f"Created 'other' mod info: {mod_info.name}".encode('utf-8').decode('ascii', errors='ignore'))
        return mod_info

    @staticmethod
    def _create_fallback_mod_info(zf: zipfile.ZipFile, info_file_path: str, mod_type: ModType,
                                  error_message: str) -> ModInfo:
        """Creates a ModInfo object when JSON parsing fails."""
        logger.error(f"Creating fallback ModInfo for {zf.filename} due to: {error_message}")

        try:
            mod_name = os.path.basename(zf.filename).replace(".zip", "")  # Fallback name
        except:
            mod_name = "Unknown Mod"

        preview_images = []
        base_dir = os.path.dirname(info_file_path) if info_file_path else ""
        file_list = zf.namelist()

        for image_ext in ('.png', '.jpg', '.jpeg'):
            if info_file_path:
                potential_image_path = os.path.join(base_dir, "preview" + image_ext).replace('\\', '/')
                if potential_image_path in file_list:
                    try:
                        with zf.open(potential_image_path) as img:
                            preview_images.append((os.path.basename(potential_image_path), img.read()))
                            logger.debug(f"Found fallback image {potential_image_path}")
                            if len(preview_images) >= 3:
                                break
                    except Exception as e:
                        logger.warning(f"Could not load fallback image {potential_image_path}: {e}")

            if len(preview_images) < 3:
                for file_name in file_list:
                    if file_name.lower().endswith(image_ext):
                        try:
                            with zf.open(file_name) as img:
                                preview_images.append((os.path.basename(file_name), img.read()))
                                logger.debug(f"Found fallback image {file_name}")
                                if len(preview_images) >= 3:
                                    break
                        except Exception as e:
                            logger.warning(f"Could not load fallback image {file_name}: {e}")


        mod_info = ModInfo(
            name=mod_name,
            author="Unknown (JSON Error)",
            type=mod_type,
            description=f"Error parsing info.json: {error_message}\n\nCould not load mod details.",
            preview_images=preview_images,
            additional_info={}
        )
        logger.info(f"Created fallback mod info: {mod_info.name}".encode('utf-8').decode('ascii', errors='ignore'))
        return mod_info