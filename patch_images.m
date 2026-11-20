% 1. Define the folder where your images are located
imageFolder = 'D:\WORK\Tools\uRheo\3DFM\Experiment\Data\Calibration\2026-09-25\2p5mMSucrose_2p8umBeads_30reps\Set1'; % Replace with your actual path
outputVideoName = 'Calibration_260925_2p5MSucrose_2p8umNoPEG_30reps_1.mp4';    % Name of the output video file
imageExtension = '*.jpg';            % Change to '*.jpg' or other format if needed

% 2. Get a list of all image files in the folder
imageFiles = dir(fullfile(imageFolder, imageExtension));
numImages = size(imageFiles,1); %length(imageFiles);

% 3. Create a VideoWriter object and set properties
outputVideo = VideoWriter(outputVideoName, 'MPEG-4'); % Use 'MPEG-4' for .mp4
outputVideo.FrameRate = 70; % Adjust the frame rate (frames per second) as needed

% 4. Open the video writer object for writing
open(outputVideo);

% 5. Loop through each image, read it, and write it to the video
for i = 1:numImages
    % Read the current image
    currentImageName = imageFiles(i).name;
    currentImagePath = fullfile(imageFolder, currentImageName);
    currentImage = imread(currentImagePath);
    
    % Write the image to the video file
    writeVideo(outputVideo, currentImage);
end

% 6. Close the video writer object
close(outputVideo);
disp(['Video successfully created: ' outputVideoName]);