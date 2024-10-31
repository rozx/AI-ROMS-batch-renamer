import pinyin from "pinyin";
import { program } from "commander";
import { version } from "../package.json";
import { readdirSync, statSync, renameSync, existsSync } from "fs";
import path from "path";
import {
	isFileIsBeingRenamed,
	trimFileName,
	isSystemOrHiddenFile,
	fileNameDuplicateRegEx,
	getRegionInfo,
	unzipAndRenameFile,
	renameFile,
} from "./utils";
import { unlink } from "fs/promises";

program
	.name("rom-batch-renamer")
	.description(
		"批量重命名Rom文件为拼音首字母+原文件名 (Batch rename files to pinyin initials)"
	)
	.version(version);

program
	.command("rename")
	.description(
		"批量重命文件夹中的文件为拼音首字母+原文件名 (Batch rename files to pinyin initials)"
	)
	.argument("[dir]", "文件夹路径 (Directory path)")
	.option(
		"-d, --dry-run",
		"仅显示重命名后的文件名，不实际重命名 (Display the renamed file names without actually renaming them)"
	)
	.option(
		"-n, --name-only",
		"仅显示重命名后的文件名，不输出其他信息 (Display the renamed file names only, without other information)"
	)
	.option(
		"-r, --recursive",
		"递归重命名文件夹中的所有文件 (Recursively rename all files in the directory)"
	)
	.option(
		"-t, --trim",
		"去除文件名中的空格与括号中的信息 (Remove spaces and content in brackets in file names)"
	)
	.option(
		"-f, --force",
		"强制重命名文件，即使文件名已经被命名过了 (Force rename files even if the file name already being renamed)"
	)
	.option(
		"-fl, --files <files...>",
		"只重命名文件，不重命名文件夹,以空格分隔 (Only rename files, not folders, separated by spaces)"
	)
	.option(
		"-e, --excludes <extension name...>",
		"排除特定的文件后缀名，以空格分隔 (Filer out certain files by extensions, separated by spaces)"
	)
	.option(
		"-i, --includes <extension name...>",
		"只重命名特定的文件后缀名，以空格分隔 (Only rename certain files by extensions, separated by spaces)"
	)
	.option(
		"-u, --unzip [password]",
		"解压并重命名zip文件 (Unzip and rename zip files)"
	)
	.action(async (dir, options) => {
		let filesList: string[] = [];
		const targetPaths: string[] = [];

		if (options.files && options.files.length > 0) {
			const files: string[] = options.files;

			if (!files.length || files.length == 0) return;
			filesList = files;
		} else {
			if (!dir) {
				console.log("Please provide a directory path.");
				return;
			}

			readdirSync(dir).forEach((file: string) => {
				filesList.push(path.join(dir, file));
			});
		}

		if (options.excludes) {
			const excludes: string[] = options.excludes;
			filesList = filesList.filter((file) => {
				const extName = path.extname(file);
				return !excludes.includes(extName);
			});
		}

		if (options.includes) {
			const includes: string[] = options.includes;
			filesList = filesList.filter((file) => {
				const extName = path.extname(file);
				return includes.includes(extName);
			});
		}

		filesList.forEach(async (filePath: string) => {
			const dir = path.dirname(filePath);
			let file = path.basename(filePath);

			if (!existsSync(filePath)) {
				if (!options.nameOnly) console.log(`File not found: ${filePath}`);
				return;
			}

			const stats = statSync(filePath);

			let newFileName: string = file;
			let newFilePath: string = filePath;
			let extName = path.extname(file);

			if (stats.isDirectory() && options.recursive) {
				// 递归重命名文件夹中的所有文件
				program.parse([
					"rename",
					filePath,
					...(options.dryRun ? ["-d"] : []),
					...(options.recursive ? ["-r"] : []),
					...(options.trim ? ["-t"] : []),
					...(options.nameOnly ? ["-n"] : []),
					...(options.force ? ["-f"] : []),
					...(options.excludes ? ["-e"] : []),
					...(options.includes ? ["-i"] : []),
					...(options.includes ? ["-u"] : []),
				]);
			} else if (stats.isFile()) {
				// check if the file is already being renamed
				if (!options.force && isFileIsBeingRenamed(file)) {
					if (!options.nameOnly)
						console.log(`Skipped: ${filePath} (Already renamed)`);
					return;
				}

				if (isSystemOrHiddenFile(file)) {
					// if (!options.nameOnly)
					// 	console.log(`Skipped: ${filePath} (Hidden or system file)`);
					return;
				}

				// grab the region info
				const regionInfo = getRegionInfo(newFileName);

				// Check if the file name needs to be trimmed
				if (options.trim) {
					newFileName = trimFileName(newFileName);
					newFilePath = path.join(dir, newFileName);
				}

				// get basename
				let baseName = path.basename(newFileName, extName);

				// adds region info to the file name
				newFileName = regionInfo
					? `${baseName} - ${regionInfo}${extName}`
					: newFileName;

				// adds pinyin initials to the file name

				const pinyinInitials = pinyin(newFileName, {
					style: pinyin.STYLE_FIRST_LETTER,
					heteronym: false,
				})[0][0]
					.substring(0, 1)
					.toUpperCase();

				newFileName = `${pinyinInitials} ${newFileName}`;
				newFilePath = path.join(dir, newFileName);

				// check if the file name already exists

				let index = 0;
				baseName = path.basename(newFileName, extName);

				while (existsSync(newFilePath) || targetPaths.includes(newFilePath)) {
					index++;

					if (!fileNameDuplicateRegEx.test(newFileName)) {
						newFileName = `${baseName} - (${index})${extName}`;
					} else {
						newFileName = newFileName.replace(
							fileNameDuplicateRegEx,
							`- (${index})${extName}`
						);
					}

					newFilePath = path.join(dir, newFileName);
				}

				if (extName === ".zip") {
					if (options.unzip) {
						try {
							// unzip and rename the file
							const unzippedFiles = await unzipAndRenameFile(
								filePath,
								newFilePath,
								options.unzip,
								Boolean(options.dryRun),
								Boolean(options.nameOnly)
							);

							// finally delete the zip file

							if (!options.dryRun) await unlink(filePath);

							if (unzippedFiles) {
								targetPaths.push(...unzippedFiles);
							}
						} catch (error: any) {
							console.log(
								`Error when unzipping file (${filePath}): ${error.message}`
							);
							return;
						}

						return;
					}
				}

				// rename the file
				await renameFile(
					filePath,
					newFilePath,
					Boolean(options.dryRun),
					Boolean(options.nameOnly)
				);

				targetPaths.push(newFilePath);
			}
		});
	});

program
	.command("revert")
	.description("还原文件名 (Revert file names)")
	.argument("<dir>", "文件夹路径 (Directory path)")
	.option(
		"-d, --dry-run",
		"仅显示还原后的文件名，不实际还原 (Display the reverted file names without actually reverting them)"
	)
	.option(
		"-r, --recursive",
		"递归还原文件夹中的所有文件 (Recursively revert all files in the directory)"
	)
	.action((dir, options) => {
		const files = readdirSync(dir);

		files.forEach((file: string) => {
			const filePath = path.join(dir, file);
			const stats = statSync(filePath);

			let newFileName: string = file;
			let newFilePath: string = filePath;

			if (stats.isDirectory() && options.recursive) {
				// 递归重命名文件夹中的所有文件
				program.parse([
					"rename",
					filePath,
					...(options.dryRun ? ["-d"] : []),
					...(options.recursive ? ["-r"] : []),
				]);
			} else if (stats.isFile()) {
				if (!isFileIsBeingRenamed(file)) {
					console.log(`Skipped: ${filePath} (Hasn't renamed)`);
					return;
				}

				if (isSystemOrHiddenFile(file)) {
					console.log(`Skipped: ${filePath} (Hidden or system file)`);
					return;
				}

				newFileName = newFileName.substring(2);
				newFilePath = path.join(dir, newFileName);

				if (options.dryRun) {
					console.log(`Revert Preview: ${filePath} -> ${newFileName}`);
				} else {
					renameSync(filePath, newFilePath);
					console.log(`Reverted: ${filePath} -> ${newFileName}`);
				}
			}
		});
	});

program.parse(process.argv);
