from Modules import Module
import logging

class Index(Module):
    def __init__(self, module_id, is_docker = False):
        super(Index, self).__init__(module_id, is_docker)
        self.output_keys = ["bam_idx"]

    def define_input(self):
        self.add_argument("bam",        is_required=True)
        self.add_argument("samtools",   is_required=True, is_resource=True)
        self.add_argument("nr_cpus",    is_required=True, default_value=3)
        self.add_argument("mem",        is_required=True, default_value=10)

    def define_output(self):

        # Get arguments value
        bams = self.get_argument("bam")

        # Check if the input is a list
        if isinstance(bams, list):
            bams_idx = [bam + ".bai" for bam in bams]
        else:
            bams_idx = bams + ".bai"

        # Add new bams as output
        self.add_output("bam_idx", bams_idx, is_path=True)

    def define_command(self):
        # Define command for running samtools index from a platform
        bam         = self.get_argument("bam")
        samtools    = self.get_argument("samtools")
        bam_idx     = self.get_output("bam_idx")

        # Generating indexing command
        cmd = ""
        if isinstance(bam, list):
            for b_in, b_out in zip(bam, bam_idx):
                cmd += "{0} index {1} {2} !LOG3! & ".format(samtools, b_in, b_out)
            cmd += "wait"
        else:
            cmd = "{0} index {1} {2} !LOG3!".format(samtools, bam, bam_idx)
        return cmd


class Flagstat(Module):
    def __init__(self, module_id, is_docker = False):
        super(Flagstat, self).__init__(module_id, is_docker)
        self.output_keys = ["flagstat"]

    def define_input(self):
        self.add_argument("bam",        is_required=True)
        self.add_argument("bam_idx",    is_required=True)
        self.add_argument("samtools",   is_required=True, is_resource=True)
        self.add_argument("nr_cpus",    is_required=True, default_value=2)
        self.add_argument("mem",        is_required=True, default_value=5)

    def define_output(self):
        # Declare bam index output filename
        flagstat = self.generate_unique_file_name(".flagstat.out")
        self.add_output("flagstat", flagstat, is_path=True)

    def define_command(self):
        # Define command for running samtools index from a platform
        bam         = self.get_argument("bam")
        samtools    = self.get_argument("samtools")
        flagstat    = self.get_output("flagstat")

        # Generating Flagstat command
        cmd = "{0} flagstat {1} > {2}".format(samtools, bam, flagstat)
        return cmd


class Idxstats(Module):
    def __init__(self, module_id, is_docker = False):
        super(Idxstats, self).__init__(module_id, is_docker)
        self.output_keys = ["idxstats"]

    def define_input(self):
        self.add_argument("bam",        is_required=True)
        self.add_argument("bam_idx",    is_required=True)
        self.add_argument("samtools",   is_required=True, is_resource=True)
        self.add_argument("nr_cpus",    is_required=True, default_value=2)
        self.add_argument("mem",        is_required=True, default_value=5)

    def define_output(self):
        # Declare bam idxstats output filename
        idxstats = self.generate_unique_file_name(extension=".idxstats.out")
        self.add_output("idxstats", idxstats)

    def define_command(self):
        # Define command for running samtools idxstats from a platform
        bam         = self.get_argument("bam")
        samtools    = self.get_argument("samtools")
        idxstats    = self.get_output("idxstats")

        # Generating Idxstats command
        cmd = "{0} idxstats {1} > {2}".format(samtools, bam, idxstats)
        return cmd


class View(Module):
    def __init__(self, module_id, is_docker=False):
        super(View, self).__init__(module_id, is_docker)
        self.output_keys = ["bam", "bam_idx", "read_count_file"]

    def define_input(self):
        self.add_argument("bam",            is_required=True)
        self.add_argument("bam_idx",        is_required=True)
        self.add_argument("samtools",       is_required=True, is_resource=True)
        self.add_argument("nr_cpus",        is_required=True, default_value=4)
        self.add_argument("mem",            is_required=True, default_value=6)
        self.add_argument("count_reads",    is_required=False, default_value=False)
        self.add_argument("bed",            is_required=False, is_resource=True)
        self.add_argument("location",       is_required=False)
        self.add_argument("exclude_flag",   is_required=False)
        self.add_argument("include_flag",   is_required=False)
        self.add_argument("outfmt",         is_required=True, default_value="b")

    def define_output(self):
        # generate file name for read counts only if the user asked for it
        if self.get_argument("count_reads"):
            count_file = self.generate_unique_file_name(extension=".read_counts.txt")
            self.add_output("read_count_file", count_file)
        else:
            bam_out = self.generate_unique_file_name(extension=".bam")
            bam_idx = "%s.bai" % bam_out
            self.add_output("bam",      bam_out)
            self.add_output("bam_idx",  bam_idx)

    def define_command(self):
        # Define command for running samtools view from a platform
        bam             = self.get_argument("bam")
        location        = self.get_argument("location")
        samtools        = self.get_argument("samtools")
        nr_cpus         = self.get_argument("nr_cpus")
        exclude_flag    = self.get_argument("exclude_flag")
        include_flag    = self.get_argument("include_flag")
        outfmt          = self.get_argument("outfmt")
        count_reads     = self.get_argument("count_reads")
        bed             = self.get_argument("bed")

        # genomic regions in the BED file and as location are not allowed at the same time
        if bed is not None and location is not None:
            logging.error("BED file and location can not be provided at the same time. Advise to use either of them.")

        # Create base samtools view command
        cmd = "%s view -@ %d -%s %s" % (samtools, nr_cpus, outfmt, bam)

        # Add include/exclude flags
        if exclude_flag is not None:
            cmd = "%s -F %s" % (cmd, exclude_flag)

        if include_flag is not None:
            cmd = "%s -f %s" % (cmd, include_flag)

        # Add commands to subset on region given in the BED file
        if bed is not None:
            cmd = "%s -L %s" % (cmd, bed)

        # Add commands to subset region
        if location is not None:
            if isinstance(location, list):
                reg = " ".join(location)
            else:
                reg = location
            cmd = "%s %s " % (cmd, reg)

        # Add command to only count the overlap reads and not print the overlapping reads to a file
        if count_reads:
            count_file = self.get_output("read_count_file")
            count_cmd = "%s -c > %s" % (cmd, count_file)
            return "%s !LOG2!" % count_cmd
        else:
            bam_out = self.get_output("bam")
            bam_out_idx = self.get_output("bam_idx")

            # Generating samtools view command
            view_cmd = "%s > %s" % (cmd, bam_out)

            # Generating samtools index command
            index_cmd = "%s index %s %s" % (samtools, bam_out, bam_out_idx)

            # Combine both into single command
            return "%s !LOG2! && %s !LOG2!" % (view_cmd, index_cmd)


class Depth(Module):
    def __init__(self, module_id, is_docker=False):
        super(Depth, self).__init__(module_id, is_docker)
        self.output_keys    = ["samtools_depth"]

    def define_input(self):
        self.add_argument("bam",        is_required=True)
        self.add_argument("bam_idx",    is_required=True)
        self.add_argument("samtools",   is_required=True,   is_resource=True)
        self.add_argument("nr_cpus",    is_required=True,   default_value=1)
        self.add_argument("mem",        is_required=True,   default_value=3)
        self.add_argument("location",   is_required=False)

    def define_output(self):
        # Declare samtools depth out filename
        samtools_depth_out = self.generate_unique_file_name(extension=".samtools_depth.out")
        self.add_output("samtools_depth", samtools_depth_out)

    def define_command(self):
        # Get arguments for generating command
        bam                 = self.get_argument("bam")
        samtools            = self.get_argument("samtools")
        chrm                = self.get_argument("location")
        samtools_depth_out  = self.get_output("samtools_depth")
        # Get depth of single chromosome/region
        if chrm is not None:
            return "%s depth -r %s -a %s > %s !LOG2!" % (samtools, chrm, bam, samtools_depth_out)
        # Get depth of entire bam
        return "%s depth -a %s > %s !LOG2!" % (samtools, bam, samtools_depth_out)


class Fastq(Module):
    def __init__(self, module_id, is_docker=False):
        super(Fastq,self).__init__(module_id, is_docker)
        self.output_keys    = ["R1", "R2"]

    def define_input(self):
        self.add_argument("bam",            is_required=True)
        self.add_argument("bam_idx",        is_required=True)
        self.add_argument("samtools",       is_required=True,   is_resource=True)
        self.add_argument("nr_cpus",        is_required=True,   default_value=4)
        self.add_argument("mem",            is_required=True,   default_value=10)
        self.add_argument("exclude_flag",   is_required=False)
        self.add_argument("include_flag",   is_required=False)

    def define_output(self):
        # Generate unique fastq paths
        R1 = self.generate_unique_file_name(extension=".R1.fastq")
        R2 = self.generate_unique_file_name(extension=".R2.fastq")

        # Add files to output
        self.add_output("R1", R1)
        self.add_output("R2", R2)

    def define_command(self):
        # Get arguments for generating command
        bam         = self.get_argument("bam")
        samtools    = self.get_argument("samtools")
        nr_cpus     = self.get_argument("nr_cpus")
        include     = self.get_argument("include_flag")
        exclude     = self.get_argument("exclude_flag")

        # Get output paths for R1 and R2
        R1 = self.get_output("R1")
        R2 = self.get_output("R2")

        # Generate options list
        opts = [
            "-@ {0}".format(nr_cpus),
            "-1 {0}".format(R1),
            "-2 {0}".format(R2)
        ]

        # Add include/exclude flags if present
        if include is not None:
            opts.append("-f {0}".format(include))
        if exclude is not None:
            opts.append("-F {0}".format(exclude))

        # Generate command for obtaining the FASTQ reads
        return "{0} fastq {1} {2} !LOG3!".format(samtools, " ".join(opts), bam)
